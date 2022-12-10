# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero

class NotaCredito(models.Model):
    _inherit = 'account.invoice'

    monto_asignado_pos = fields.Integer(string='Monto Asignado en POS')



class POSPagos(models.TransientModel):
    _inherit = 'pos.make.payment'

    banco_id = fields.Many2one(comodel_name='res.bank', string='Banco')
    nombre_propietario = fields.Char(string='Propietario Cheque')
    cuenta_bancaria = fields.Char(string='N° Cuenta')
    numero_cheque = fields.Char(string='N° Cheque')
    fecha_cheque = fields.Date(string='Fecha Cheque')
    es_cheque = fields.Boolean(string='Cueques X Cobrar?',related='journal_id.es_cheque')
    es_credito = fields.Boolean(string='Crédito Cliente?',related='journal_id.es_credito')
    aplicar_nc = fields.Boolean(string='Aplica NC?',related='journal_id.aplicar_nc')
    nota_credito_id = fields.Many2one(comodel_name='account.invoice', string='Nota Crédito',domain="[('document_class_id', '=', 13)]" )
    valor_nc = fields.Integer(string='Valor Nota Crédito')
    monto_asignado_pos = fields.Integer(string='Monto Asignado en POS',related='nota_credito_id.monto_asignado_pos')

    @api.multi
    def check(self):
        order=super(POSPagos,self).check()   
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        partner_id_saldo_credito=order.partner_id.saldo_linea_credito
        if order.journal_document_class_id.sii_document_class_id.sii_code==61 and self.nota_credito_id:        
            self.nota_credito_id.monto_asignado_pos+=self.amount

    @api.onchange('nota_credito_id')
    def _onchange_nota_credito_id(self):
        if self.nota_credito_id:
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            if order.partner_id.id==self.nota_credito_id.partner_id.id:
                self.valor_nc=self.nota_credito_id.amount_total-self.nota_credito_id.monto_asignado_pos
            else:
                raise ValidationError('Nota de crédito no pertenece al cliente %s '%(order.partner_id.name))

    
    @api.constrains('amount')
    def check_saldo_credito(self):
        if self.es_credito:
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            partner_id_saldo_credito=order.partner_id.saldo_linea_credito
            if order.journal_document_class_id.sii_document_class_id.sii_code!=61:
                if order.partner_saldo_favor!=0:
                    if self.amount>order.partner_saldo_favor:
                        raise ValidationError('Saldo a favor %s no alcanza para pagar la orden '%(order.partner_saldo_favor))
                else:
                    if order.partner_id.tiene_credito:
                        if self.amount>partner_id_saldo_credito:
                            raise ValidationError('Saldo de crédito %s no alcanza para pagar la orden '%(partner_id_saldo_credito))
                    else:
                        raise ValidationError('Cliente %s no tiene habilitada la forma de pago crédito '%(order.partner_id.name))
        if self.aplicar_nc:
            if self.amount>(self.nota_credito_id.amount_total-self.nota_credito_id.monto_asignado_pos):
                raise ValidationError('Valor nota de crédito %s no alcanza para pagar la orden '%(self.valor_nc))
