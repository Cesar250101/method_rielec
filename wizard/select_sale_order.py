# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SelectProducts(models.TransientModel):
    _name = 'method_rielec.select_sale_order'

    sale_order_ids = fields.Many2many(comodel_name='sale.order', string='Presupuestos')

    @api.multi
    def select_sale_order(self):
        tax=[]
        order_id = self.env['pos.order'].browse(self._context.get('active_id', False))
        order_ids=[]
        for sale in self.sale_order_ids:
            order_ids.append(sale.id)
            order_id.partner_id=sale.partner_id.id
            for l in sale.order_line:
                tax = [(6, 0, [x.id for x in l.product_id.taxes_id])]
                # price = order_id.pricelist_id.get_product_price(l, 1.0, order_id.partner_id)
                location_id=order_id.location_id.id
                stock=self.env['stock.quant'].search([('product_id','=',l.product_id.id),('location_id','=',location_id)],limit=1).quantity
                self.env['pos.order.line'].create({
                        'product_id': l.product_id.id,                        
                        'product_uom': l.product_id.uom_id.id,
                        'qty':l.product_uom_qty,
                        'price_unit': l.price_unit,
                        'price_subtotal': l.price_subtotal,
                        'price_subtotal_incl':l.price_subtotal,
                        'order_id': order_id.id,
                        'tax_ids':tax,
                        'stock_product':stock,
                        'location_id':order_id.location_id.id
                    })
        order_id.write(
            {'sale_order_ids':[(6,0,order_ids)]}
        )
        order_id._onchange_amount_line_all()
        order_id._onchange_amount_all()
