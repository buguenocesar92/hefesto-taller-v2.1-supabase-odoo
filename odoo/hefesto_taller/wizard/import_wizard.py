import base64, hashlib, json, re
from odoo import models, fields
from odoo.exceptions import UserError

class ImportWizard(models.TransientModel):
    _name = 'hefesto.taller.import'
    _description = 'Importar respaldo de Hefesto'
    payload = fields.Binary(required=True)
    filename = fields.Char()
    update_existing = fields.Boolean(string='Actualizar órdenes previamente importadas', default=False)
    dry_run = fields.Boolean(string='Solo validar y contar (sin importar)', default=True)
    report = fields.Text(readonly=True)

    def action_import(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise UserError('Solo administradores pueden importar respaldos.')
        raw = base64.b64decode(self.payload)
        if len(raw) > 100*1024*1024:
            raise UserError('El respaldo supera 100 MB.')
        try:
            payload = json.loads(raw)
            s = payload.get('state', payload)
            for key in ('customers','inventory','orders'):
                if not isinstance(s.get(key), list):
                    raise ValueError(key)
            customers = {c['id'] for c in s['customers']}
            seen = set()
            for o in s['orders']:
                if o['id'] in seen or o['customerId'] not in customers or o['status'] not in ['Recibido','Diagnóstico','Por aprobar','En reparación','Listo','Entregado']:
                    raise ValueError('orden inválida')
                seen.add(o['id'])
                for l in o['lines']:
                    if l['qty'] <= 0 or l['price'] < 0:
                        raise ValueError('línea inválida')
        except (ValueError, KeyError, TypeError):
            raise UserError('Respaldo inválido. Exporta JSON v2 desde Hefesto.')
        company = self.env.company
        if company.currency_id.name != 'CLP':
            raise UserError('Selecciona una empresa con moneda CLP antes de importar.')
        report = '%s clientes, %s productos, %s órdenes. No genera contabilidad ni existencias.' % (len(s['customers']), len(s['inventory']), len(s['orders']))
        if not self.dry_run:
            def upsert(kind, source, model, values):
                key = 'c%s_%s_%s' % (company.id, kind, re.sub('[^a-zA-Z0-9_]', '_', str(source)))
                record = self.env.ref('hefesto_taller_data.' + key, raise_if_not_found=False)
                if not record:
                    record = self.env[model].create(values)
                    self.env['ir.model.data'].create({'module':'hefesto_taller_data','name':key,'model':model,'res_id':record.id,'noupdate':True})
                elif self.update_existing:
                    record.write(values)
                return record
            partners = {}
            for kind, collection in [('customer',s['customers']), ('supplier',s.get('suppliers',[]))]:
                for c in collection:
                    rec = upsert(kind,c['id'],'res.partner',{'name':c['name'],'email':c.get('email'),'phone':c.get('phone'),'comment':'RUT origen: '+c.get('rut','')+'\n'+c.get('notes',''),'company_id':company.id})
                    if kind == 'customer': partners[c['id']] = rec.id
            for p in s['inventory']:
                upsert('product',p['id'],'product.template',{'name':p['name'],'default_code':p.get('sku'),'list_price':p['price'],'company_id':company.id})
            for o in s['orders']:
                values={'name':'OT-'+o['id'],'source_id':o['id'],'company_id':company.id,'partner_id':partners[o['customerId']],'device':o['device'],'serial':o.get('serial'),'stage':o['status'],'cancelled':bool(o.get('cancelled')),'technician':o.get('technician'),'issue':o.get('issue'),'diagnosis':o.get('diagnosis'),'due':o.get('due') or False,'source_json':json.dumps(o,ensure_ascii=False)}
                existing=self.env['hefesto.taller.order'].search([('source_id','=',o['id']),('company_id','=',company.id)],limit=1)
                if existing and not self.update_existing: continue
                rec=existing or self.env['hefesto.taller.order'].create(values)
                if existing: rec.write(values)
                rec.line_ids.unlink(); rec.payment_ids.unlink()
                for l in o['lines']:
                    self.env['hefesto.taller.line'].create({'order_id':rec.id,'name':l['description'],'quantity':l['qty'],'price':l['price']})
                for p in o.get('payments',[]):
                    self.env['hefesto.taller.payment'].create({'order_id':rec.id,'reference':p['id'],'date_text':p.get('date'),'method':p.get('method'),'amount':p['amount']})
            checksum=hashlib.sha256(raw).hexdigest()
            if not self.env['hefesto.taller.snapshot'].search_count([('checksum','=',checksum),('company_id','=',company.id)]):
                self.env['hefesto.taller.snapshot'].create({'name':self.filename or 'hefesto.json','company_id':company.id,'checksum':checksum,'payload':self.payload,'report':report})
            report='Importación terminada. '+report
        else: report='Validación sin cambios. '+report
        self.report=report
        return {'type':'ir.actions.act_window','res_model':self._name,'res_id':self.id,'view_mode':'form','target':'new'}
