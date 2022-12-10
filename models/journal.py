# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class Usuarios(models.Model):
    _inherit = 'account.journal'

    es_cheque = fields.Boolean(string='Cueques X Cobrar?')
    es_credito = fields.Boolean(string='Crédito Clientes?')
    aplicar_nc = fields.Boolean(string='Aplicar NC?',help='Indica si se aplica el valor de una nota de crédito al pago de una venta')

    