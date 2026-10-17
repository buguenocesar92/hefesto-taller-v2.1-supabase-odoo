from odoo import models, fields, api
from math import floor

class Order(models.Model):
    _name = 'hefesto.taller.order'
    _description = 'Orden de taller Hefesto'
    _order = 'id desc'
    name = fields.Char(required=True)
    source_id = fields.Char(required=True, index=True, copy=False)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', required=True)
    device = fields.Char(required=True)
    serial = fields.Char()
    stage = fields.Selection([(v,v) for v in ['Recibido','Diagnóstico','Por aprobar','En reparación','Listo','Entregado']], default='Recibido', required=True)
    cancelled = fields.Boolean()
    technician = fields.Char()
    issue = fields.Text()
    diagnosis = fields.Text()
    due = fields.Date()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    line_ids = fields.One2many('hefesto.taller.line', 'order_id')
    payment_ids = fields.One2many('hefesto.taller.payment', 'order_id')
    source_json = fields.Text(groups='base.group_system', readonly=True)
    total = fields.Monetary(compute='_compute_totals')
    paid = fields.Monetary(compute='_compute_totals')
    _sql_constraints = [('source_company_unique', 'unique(source_id, company_id)', 'La orden ya existe en esta empresa.')]

    @api.depends('line_ids.quantity', 'line_ids.price', 'payment_ids.amount')
    def _compute_totals(self):
        for rec in self:
            rec.total = floor(sum(l.quantity*l.price for l in rec.line_ids)*1.19+0.5)
            rec.paid = sum(p.amount for p in rec.payment_ids)

class Line(models.Model):
    _name = 'hefesto.taller.line'
    _description = 'Concepto de reparación Hefesto'
    order_id = fields.Many2one('hefesto.taller.order', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True)
    name = fields.Char(required=True)
    quantity = fields.Float(default=1)
    price = fields.Float()

class Payment(models.Model):
    _name = 'hefesto.taller.payment'
    _description = 'Pago histórico Hefesto (no contable)'
    order_id = fields.Many2one('hefesto.taller.order', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True)
    reference = fields.Char()
    date_text = fields.Char()
    method = fields.Char()
    amount = fields.Float()

class Snapshot(models.Model):
    _name = 'hefesto.taller.snapshot'
    _description = 'Respaldo importado de Hefesto'
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    checksum = fields.Char(index=True, required=True)
    payload = fields.Binary(attachment=True, required=True)
    report = fields.Text()
