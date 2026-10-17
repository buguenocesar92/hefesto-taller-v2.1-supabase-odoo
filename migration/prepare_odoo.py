#!/usr/bin/env python3
"""Prepare offline Odoo import CSVs; never contacts Odoo or posts accounting."""
import argparse,csv,json,re,pathlib,hashlib

def prepare(source,out):
    payload=json.loads(pathlib.Path(source).read_text());s=payload.get('state',payload)
    for k in ('customers','inventory','orders'): 
        if not isinstance(s.get(k),list): raise ValueError('Respaldo inválido: '+k)
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    def xid(kind,value): return 'hefesto_taller_data.'+kind+'_'+re.sub('[^a-zA-Z0-9_]','_',str(value))
    def write(name,headers,rows):
        with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(headers);w.writerows(rows)
    write('01_clientes.csv',['id','name','email','phone','comment'],[[xid('customer',c['id']),c['name'],c.get('email',''),c.get('phone',''),'RUT origen: '+c.get('rut','')+'\n'+c.get('notes','')] for c in s['customers']])
    write('02_proveedores.csv',['id','name','email','phone','comment'],[[xid('supplier',c['id']),c['name'],c.get('email',''),c.get('phone',''),'RUT origen: '+c.get('rut','')+'\n'+c.get('notes','')] for c in s.get('suppliers',[])])
    write('03_productos.csv',['id','name','default_code','list_price'],[[xid('product',p['id']),p['name'],p['sku'],p['price']] for p in s['inventory']])
    write('04_stock_conciliar.csv',['source_id','sku','name','quantity','minimum','unit_cost'],[[p['id'],p['sku'],p['name'],p['stock'],p['min'],p.get('cost','')] for p in s['inventory']])
    write('05_ordenes_conciliar.csv',['source_id','customer_external_id','device','serial','status','cancelled','created','due','net','gross','paid'],[[o['id'],xid('customer',o['customerId']),o['device'],o.get('serial',''),o['status'],o.get('cancelled',False),o['created'],o['due'],sum(l['qty']*l['price'] for l in o['lines']),int(sum(l['qty']*l['price'] for l in o['lines'])*1.19+.5),sum(p['amount'] for p in o['payments'])] for o in s['orders']])
    write('06_pagos_conciliar.csv',['source_id','order_id','date','method','amount'],[[p['id'],o['id'],p['date'],p['method'],p['amount']] for o in s['orders'] for p in o['payments']])
    (out/'hefesto-completo.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    summary={'source_sha256':hashlib.sha256(pathlib.Path(source).read_bytes()).hexdigest(),'customers':len(s['customers']),'products':len(s['inventory']),'orders':len(s['orders']),'payments':sum(len(o['payments']) for o in s['orders']),'mode':'offline; no accounting or stock posting'}
    (out/'manifest.json').write_text(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');args=parser.parse_args();print(json.dumps(prepare(args.source,args.output),indent=2))
