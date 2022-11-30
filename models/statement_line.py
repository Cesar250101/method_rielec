# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class LineasPagos(models.Model):
    _inherit = 'account.bank.statement.line'

    banco_id = fields.Many2one(comodel_name='res.bank', string='Banco')
    nombre_propietario = fields.Char(string='Propietario Cheque')
    cuenta_bancaria = fields.Char(string='N° Cuenta')
    numero_cheque = fields.Char(string='N° Cheque')
    fecha_cheque = fields.Date(string='Fecha Cheque')
    es_cheque = fields.Boolean(string='Cueques X Cobrar?',related='journal_id.es_cheque')