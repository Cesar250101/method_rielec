# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class Usuarios(models.Model):
    _inherit = 'res.partner'

    tiene_credito = fields.Boolean(string='Tiene Crédito?')
    linea_credito = fields.Float('Línea de Crédito')
    dias_prorroga = fields.Integer('Días Prorroga')
    monto_deuda = fields.Float(compute='_compute_monto_deuda', string='Monto Deuda', store=True)
    saldo_linea_credito = fields.Float(string='Saldo Línea Crédito',compute='_compute_saldo_linea_credito',store=True)

    @api.depends('linea_credito','monto_deuda')
    def _compute_saldo_linea_credito(self):
        for s in self:
            s.saldo_linea_credito=s.linea_credito-s.monto_deuda

    @api.depends('invoice_ids')
    def _compute_monto_deuda(self):
        deuda=0
        for p in self:
            for i in p.invoice_ids:
                deuda+=i.amount_total_signed
            p.monto_deuda=deuda
