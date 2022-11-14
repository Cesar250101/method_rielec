# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class Usuarios(models.Model):
    _inherit = 'stock.picking'

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=True, required=True,domain = "[('usage','=','internal')]",
        states={'draft': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        readonly=True, required=True,domain = "[('usage','=','internal')]",
        states={'draft': [('readonly', False)]})


class Usuarios(models.Model):
    _inherit = 'pos.config'

    sucursal = fields.Selection([
        ('matriz', 'Casa Matris'),
        ('sucursal', 'Sucursal'),
    ], string='Sucursal')

    

class Partner(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _actualizar_nro_factura(self):
        document_class=self.env['sii.document_class'].search([('sii_code','=',33)],limit=1)        
        ordenes=self.env['pos.order'].search([('sii_document_number','=',0),('document_class_id','=',document_class.id)])
        for o in ordenes:
            o.sii_document_number=o.invoice_id.sii_document_number
        


class Partner(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def open_frontend_cb(self):
        if not self.ids:
            return {}
        self.user_id=self.env.uid
        for session in self.filtered(lambda s: s.user_id.id != self.env.uid):
            raise UserError(_("You cannot use the session of another user. This session is owned by %s. "
                              "Please first close this one to use this point of sale.") % session.user_id.name)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url':   '/pos/web/',
        }


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
            #Actualiza precio de venta
            product_template=self.env['product.template'].search([('id','=',l.product_id.product_tmpl_id.id)])
            precio=round((l.price_unit*(1+(product_template.producto_margen/100)))*1.19,0)
            values={
                'list_price':precio
            }
            product_template.write(values)

        

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

    @api.onchange('')
    def _onchange_(self):
        pass

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

    # @api.model
    # def _calculo_precios_venta(self):
    #     productos=self.env['product.template'].search([('producto_margen','!=',0)])
    #     for p in productos:
    #         margen=1+(p.producto_margen/100)
    #         print(margen)
    #         p.list_price=round((p.standard_price*margen)*1.19,0)
    #         print(p.list_price)
    