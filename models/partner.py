# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class Usuarios(models.Model):
    _inherit = 'res.partner'

    tiene_credito = fields.Boolean(string='Tiene Crédito?')
    linea_credito = fields.Float('Línea de Crédito')
    dias_prorroga = fields.Integer('Días Prorroga')
    monto_deuda = fields.Float(compute='_compute_monto_deuda', string='Monto Deuda', store=True)
    saldo_linea_credito = fields.Float(string='Saldo Línea Crédito',compute='_compute_saldo_linea_credito',store=True)
    vigencia_creadito = fields.Date('Vigente hasta:')
    credito_bloqueado = fields.Boolean('Crédito Bloqueado?')

    
    @api.model
    def bloquea_credito(self):    
        clientes_con_credito=self.env['res.partner'].search([('tiene_credito','=',True)])
        fecha_actual=datetime.now().date()
        for p in clientes_con_credito:
            #Si tienes facturas vencidas por más de los días de tolerancia se bloquea
            bloquea=False
            domain=[
                ('state','=','open'),                
                ('partner_id','=',p.id)
            ]
            facturas_abiertas=self.env['account.invoice'].search(domain)
            for f in facturas_abiertas:
                # fecha_vcto=f.date_due if f.date_due else fecha_actual + datetime.timedelta(days=7)
                fecha_vcto=f.date_due if f.date_due else fecha_actual + timedelta(days=7)
                if fecha_vcto<=fecha_actual:
                    bloquea=True

            if p.monto_deuda>0:
                if p.vigencia_creadito:
                    fecha_para_bloqqueo=p.vigencia_creadito + timedelta(days=7)
                    if p.monto_deuda!=0 and fecha_para_bloqqueo<=fecha_actual:
                        bloquea=True
            if bloquea:
                p.credito_bloqueado=True


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
