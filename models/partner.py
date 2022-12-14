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
            return s.saldo_linea_credito
            
    @api.depends('invoice_ids','linea_credito')
    def _compute_monto_deuda(self):
        deuda=0
        for p in self:
            journal_credito_id=self.env['account.journal'].search([('es_credito','=',True)],limit=1)
            cuenta_credito=journal_credito_id.default_debit_account_id.id
            move_line=self.env['account.move.line'].search([('account_id','=',cuenta_credito),('partner_id','=',p.id)])

            for i in move_line:
                if i.move_id.state=='posted':
                    deuda+=i.debit-i.credit
            p.monto_deuda=deuda
            return deuda
