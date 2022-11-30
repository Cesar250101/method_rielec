# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SelectProducts(models.TransientModel):
    _name = 'method_rielec.select_products'

    product_ids = fields.Many2many('product.product', string='Products')
    cantidad = fields.Integer('cantidad')
    flag_order = fields.Char('Flag Order')

    @api.multi
    def select_products(self):
        tax=[]
        if self.flag_order == 'so':
            order_id = self.env['pos.order'].browse(self._context.get('active_id', False))
            for product in self.product_ids:
                # location_ids=self.env['stock.location'].search([('usage','=','internal')])
                # stock_quant=self.env['stock.quant'].search([('location_id','in',location_ids),
                #                                             ('product_id','=',product.id)])
                tax = [(6, 0, [x.id for x in product.taxes_id])]
                price = order_id.pricelist_id.get_product_price(product, 1.0, order_id.partner_id)
                location_id=order_id.location_id.id
                stock=self.env['stock.quant'].search([('product_id','=',product.id),('location_id','=',location_id)],limit=1).quantity
                self.env['pos.order.line'].create({
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'price_unit': price,
                    'price_subtotal': round(product.lst_price/1.19),
                    'price_subtotal_incl':product.lst_price,
                    'order_id': order_id.id,
                    'tax_ids':tax,
                    'stoct_product':stock
                })
            order_id._onchange_amount_line_all()
            order_id._onchange_amount_all()
        elif self.flag_order == 'po':
            order_id = self.env['purchase.order'].browse(self._context.get('active_id', False))
            for product in self.product_ids:
                self.env['purchase.order.line'].create({
                    'product_id': product.id,
                    'name': product.name,
                    'date_planned': order_id.date_planned,
                    'product_uom': product.uom_id.id,
                    'price_unit': product.lst_price,
                    'product_qty': 1.0,
                    'order_id': order_id.id
                })