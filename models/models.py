# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ComprobantesLineas(models.Model):
    _inherit = 'account.move.line'
    _description = 'Comprobantes contables detalle'
    
    
    @api.model
    def _compute_fecha_vcto(self):
        if self.account_id.calcula_vcto:
            self.date_maturity=self.date_maturity+self.partner_id.property_payment_term_id.line_ids.days

    
class PlanCuenta(models.Model):
    _inherit = 'account.account'
    _description = 'Plan de cuentas'

    calcula_vcto = fields.Boolean('Calcula Vcto?',help='Indica su calcula la fecha de vcto desde la condición de pago del cliente')


class ProductRemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Plantilla de productos'

    producto_margen = fields.Float('% Margen s/Costo')

    @api.onchange('producto_margen')
    def _onchange_(self):        
        if self.producto_margen:
            margen=1+(self.producto_margen/100)
            precio=round(((self.standard_price*margen)*1.19),0)
            self.list_price=precio
    