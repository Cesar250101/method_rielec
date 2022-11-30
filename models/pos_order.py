# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _default_location(self):
        return self.session_id.config_id.stock_location_id.id

    # location_id = fields.Many2one(comodel_name='stock.location', 
    #                                 string='Ubicación Stock', 
    #                                 default=_default_location,
    #                                 domain=[('usage','=','internal')])
    location_id = fields.Many2one(comodel_name='stock.location', 
                                    string='Ubicación Stock', 
                                    domain=[('usage','=','internal')])    
    stoct_product = fields.Integer(string='Stock',readonly=True,store=True)
    session_id = fields.Many2one(comodel_name='pos.session', string='Cesión POS',related='order_id.session_id')

    @api.onchange('qty')
    def _onchange_qty(self):
        if self.product_id:
            res = {}            
                # Warning("No puede agregar más productos que el stock disponible, Debe agregar una segunda línea con una ubicación que tenga stock!")
            if self.stoct_product<self.qty:
                res = {'warning': {
                        'title': _('Warning'),
                        'message': _('No puede agregar más productos que el stock disponible, Debe agregar una segunda línea con una ubicación que tenga stock!')
                                    }
                    }
            if res:
                self.qty=self.stoct_product
                return res          

    @api.onchange('product_id','location_id','qty')
    def _onchange_product(self):
        if self.product_id:
            stock=0
            res = {} 
            stock_location=self.env['stock.quant'].search([('product_id','=',self.product_id.id),('location_id','=',self.location_id.id)],limit=1)
            for s in stock_location:
                stock=s.quantity
            self.stoct_product=stock
            if self.qty>stock:
                res = {'warning': {
                                'title': _('Warning'),
                                'message': _('Stock insuficiente para el producto : %s'%(self.product_id.name))
                                            }
                            }
            if res:
                self.qty=self.stoct_product
                return res                  

class PosOrder(models.Model):
    _inherit = "pos.order"

    picking_traspaso_id = fields.Many2one(comodel_name='stock.picking', string='Traspaso de Bodega')
    def _default_session(self):
        pos=[]
        pos_usuarios=self.env.user.pos_config_ids
        for s in pos_usuarios:
            pos.append(s.id)

        return self.env['pos.session'].search([('state', '=', 'opened'), 
                                                ('user_id', '=', self.env.uid),
                                                ('config_id','in',pos)
                                            ], limit=1)

    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        domain="[('state', '=', 'opened')]", 
        states={'draft': [('readonly', False)]},
        readonly=True, default=_default_session)


    @api.multi
    def action_pos_order_paid(self):
        order=super(PosOrder,self).action_pos_order_paid()        
        if self.test_paid():
            picking=self.crear_picking()
            if self.journal_document_class_id.sii_document_class_id.sii_code==33:
                factura=self.crear_factura()

    @api.multi
    def crear_factura(self):
        order_id=self
        model_account_invoice=self.env['account.invoice']
        invoice_line=[]

        for i in self.lines:
            invoice_line.append(
                            (0, 0, {
                                "product_id": i.product_id.id,
                                "quantity":i.qty,
                                "account_id":i.product_id.categ_id.property_account_income_categ_id.id,
                                "uom_id":i.product_id.product_tmpl_id.uom_id.id,
                                "name":i.product_id.product_tmpl_id.name,   
                                "price_unit":i.price_unit
                            }))
        if invoice_line:
            referencias=self._prepare_invoice()
            invoice_type = 'out_invoice' if self.amount_total >= 0 else 'out_refund'

            invoice={
                'partner_id':order_id.partner_id.id,
                'origin':order_id.name,
                'invoice_line_ids':invoice_line,
                'date_invoice':order_id.date_order.date(),
                'referencias':referencias,
                'account_id': self.partner_id.property_account_receivable_id.id,
                'journal_id': self.session_id.config_id.invoice_journal_id.id,
                'company_id': self.company_id.id,
                'reference': self.name,
                'comment': self.note or '',
                'currency_id': self.pricelist_id.currency_id.id,
                'user_id': self.user_id.id,
                'activity_description': self.partner_id.activity_description.id,
                'ticket':  self.session_id.config_id.ticket,
                'document_class_id': self.document_class_id.id,
                'journal_document_class_id': self.journal_document_class_id.id,
                'responsable_envio': self.env.uid,
                'use_documents': True,

            }
            factura_creada=model_account_invoice.create(invoice)
            factura_confirmado=factura_creada.action_invoice_open()
            order_id.write({
                'state':'invoiced',
                'invoice_id':factura_creada.id,
                'sii_batch_number':factura_creada.sii_batch_number,
                'sii_barcode':factura_creada.sii_barcode,
                'sii_xml_request':factura_creada.sii_xml_request,
                'sii_result':factura_creada.sii_result,
                'sii_document_number':factura_creada.sii_document_number,
                'sii_xml_dte':factura_creada.sii_xml_dte,
                'sii_message':factura_creada.sii_message,
                })

            #self.picking_traspaso_id=factura_creada.id
            return order_id

    @api.multi
    def _prepare_invoice(self):
        vals = super(PosOrder, self)._prepare_invoice()
        if self.partner_id.acteco_ids:
            vals["acteco_id"] = self.partner_id.acteco_ids.id
        if self.referencias:
            vals["referencias"] = []
            for ref in self.referencias:
                vals["referencias"].append(
                    (
                        0,
                        0,
                        {
                            "origen": ref.origen,
                            "sii_referencia_TpoDocRef": ref.sii_referencia_TpoDocRef.id,
                            "motivo": ref.motivo,
                            "fecha_documento": ref.fecha_documento,
                        },
                    )
                )
            return vals["referencias"]

    @api.multi
    def crear_picking(self):
        order_id=self
        model_stock_picking=self.env['stock.picking']
        picking_line=[]
        ubicacion_origen=0
        ubicacion_destino=0

        for i in self.lines:
            if i.location_id.id!=self.location_id.id:
                ubicacion_origen=i.location_id.id
                ubicacion_destino=self.location_id.id
                picking_line.append(
                            (0, 0, {
                                "product_id": i.product_id.id,
                                "product_uom_qty":i.qty,
                                "location_dest_id": self.location_id.id,
                                "location_id": i.location_id.id,
                                "product_uom":i.product_id.product_tmpl_id.uom_id.id,
                                "name":i.product_id.product_tmpl_id.name,   
                            }))
        if picking_line:
            picking_ids=[]
            picking={
                'partner_id':order_id.company_id.partner_id.id,
                "location_dest_id": ubicacion_destino,
                "location_id": ubicacion_origen,
                'origin':order_id.name,
                'move_ids_without_package':picking_line,
                'picking_type_id':5
            }
            pickng_creado=model_stock_picking.create(picking)
            pickng_confirmado=pickng_creado.action_confirm()

            # picking_ids.append(pickng_creado.id)
            # order_id.write(
            #     {
            #         "picking_ids": [(4,pickng_creado.id)]
            #     }
            # )
            self.picking_traspaso_id=pickng_creado.id
            return order_id


    @api.constrains('lines')
    def check_qty_stock(self):
        for l in self.lines:
            stock=self.env['stock.quant'].search([('product_id','=',l.product_id.id),('location_id','=',l.location_id.id)],limit=1).quantity            
            if stock<l.qty:
                raise ValidationError('Stock insuficiente para el producto %s  '%(l.product_id.name))
                
    @api.onchange('lines','amount_total')
    def _onchange_amount_line_all(self):
        for line in self.lines:
            res = line._compute_amount_line_all()
            line.update(res)

    def _prepare_bank_statement_line_payment_values(self, data):
        """Create a new payment for the order"""
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', fields.Date.context_today(self)),
            'name': self.name + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': self.env["res.partner"]._find_accounting_partner(self.partner_id).id or False,
        }

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        journal = self.env['account.journal'].browse(journal_id)
        # use the company of the journal and not of the current user
        company_cxt = dict(self.env.context, force_company=journal.company_id.id)
        account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id', 'res.partner')
        args['account_id'] = (self.partner_id.property_account_receivable_id.id) or (account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (
                    self.partner_id.name, self.partner_id.id,)
            raise UserError(msg)

        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        for statement in self.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break
        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'pos_statement_id': self.id,
            'journal_id': journal_id,
            'ref': self.session_id.name,
        })

        if data['es_cheque']==True:        
            args.update({
                    'banco_id': data['banco_id'][0],
                    'nombre_propietario': data['nombre_propietario'],
                    'cuenta_bancaria': data['cuenta_bancaria'],
                    'numero_cheque': data['numero_cheque'],
                    'fecha_cheque': data['fecha_cheque'],
                })

        return args
