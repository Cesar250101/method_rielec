# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero

class POSPagos(models.TransientModel):
    _inherit = 'pos.make.payment'

    banco_id = fields.Many2one(comodel_name='res.bank', string='Banco')
    nombre_propietario = fields.Char(string='Propietario Cheque')
    cuenta_bancaria = fields.Char(string='N° Cuenta')
    numero_cheque = fields.Char(string='N° Cheque')
    fecha_cheque = fields.Date(string='Fecha Cheque')
    es_cheque = fields.Boolean(string='Cueques X Cobrar?',related='journal_id.es_cheque')
    es_credito = fields.Boolean(string='Crédito Cliente?',related='journal_id.es_credito')

    @api.constrains('amount')
    def check_saldo_credito(self):
        if self.es_credito:
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            partner_id_saldo_credito=order.partner_id.saldo_linea_credito
            print(order.partner_id.saldo_linea_credito)
            if self.amount>partner_id_saldo_credito:
                raise ValidationError('Saldo de crédito %s no alcanza para pagar la orden '%(partner_id_saldo_credito))