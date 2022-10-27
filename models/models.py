# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Compras(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        rec= super(Compras, self).button_confirm()
        for l in self.order_line:
            product=self.env['product.product'].search([('id','=',l.product_id.id)])
            values={
                'standard_price':l.price_unit
            }
            product.write(values)
        

    @api.model
    def _actualizar_costo_desde_oc(self):
        for l in self.order_line:
            product=self.env['product.product'].search([('id','=',l.product_id.id)])
            values={
                'standard_price':l.price_unit
            }        
            product.write(values)


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

    @api.onchange('producto_margen','standard_price')
    def _onchange_producto_margen(self):        
        if self.producto_margen:
            margen=1+(self.producto_margen/100)
            precio=round(((self.standard_price*margen)*1.19),0)
            self.list_price=precio

    @api.onchange('standard_price')
    def _onchange_standard_price(self):        
        if self.producto_margen:
            margen=1+(self.producto_margen/100)
            precio=round(((self.standard_price*margen)*1.19),0)
            self.list_price=precio

    @api.model
    def _calculo_precios_venta(self):
        productos=self.env['product.template'].search([('list_price','<',10)])
        for p in productos:
            margen=1+(p.producto_margen/100)
            print(margen)
            p.price_unit=round((p.standard_price*margen)*1.19,0)
            print(p.price_unit)
    