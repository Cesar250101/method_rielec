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

    

class PosOrder(models.Model):
    _inherit = 'pos.order'

    tiene_credito = fields.Boolean(string='Tiene Crédito?', related='partner_id.tiene_credito')
    linea_credito = fields.Float(string='Línea de Crédito',related='partner_id.linea_credito')
    dias_prorroga = fields.Float('Días Prorroga')
    monto_deuda = fields.Float(string='Monto Deuda')
    saldo_linea_credito = fields.Float(string='Saldo Línea Crédito')

    journal_document_class_id = fields.Many2one(
        "account.journal.sii_document_class",
        string="Tipo Documento",
        default=lambda self: self._default_journal_document_class_id(),
        readonly=True,
        states={"draft": [("readonly", False)]},)

    @api.onchange('partner_id')
    def _onchange_(self):
        self.monto_deuda=self.partner_id._compute_monto_deuda()
        self.saldo_linea_credito=self.partner_id._compute_saldo_linea_credito()

    def _default_journal_document_class_id(self):
        if not self.env["ir.model"].search([("model", "=", "sii.document_class")]):
            return False
        if self.document_class_id:
            return self.env['account.journal.sii_document_class']
        journal = self.env["account.invoice"].default_get(["journal_id"])["journal_id"]
        default_type = self._context.get("type", "out_invoice")
        if default_type in ["in_invoice", "in_refund"]:
            return self.env["account.journal.sii_document_class"]
        dc_type = ["invoice"] if default_type in ["in_invoice", "out_invoice"] else ["credit_note", "debit_note"]
        jdc = self.env["account.journal.sii_document_class"].search(
            [("journal_id", "=", journal), ("sii_document_class_id.document_type", "in", dc_type),], limit=1
        )
        return jdc

    @api.onchange('journal_document_class_id')
    def _onchange_journal_document_class_id(self):
        try:
            self.sequence_id=self.journal_document_class_id.sequence_id
            self.document_class_id=self.journal_document_class_id.sii_document_class_id.id
        except:
            pass


    @api.model
    def _actualizar_nro_factura(self):
        document_class=self.env['sii.document_class'].search([('sii_code','=',33)],limit=1)        
        ordenes=self.env['pos.order'].search([('sii_document_number','=',0),('document_class_id','=',document_class.id)])
        for o in ordenes:
            o.sii_document_number=o.invoice_id.sii_document_number
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        try:
            self.pricelist_id=self.partner_id.property_product_pricelist.id
        except:
            pass
        
    # @api.model
    # def create(self, vals):
    #     order_id=super(PosOrder, self).create(vals)
    #     nombre_bodega_principal=self.env['stock.warehouse'].search([('lot_stock_id','=',order_id.session_id.config_id.stock_location_id.id)],limit=1).name
    #     config_location_id=order_id.session_id.config_id.stock_location_id.id
    #     picking_line=[]
    #     model_stock_picking=self.env['stock.picking']
    #     for i in order_id.lines:
    #         if i.stock_location_name!=nombre_bodega_principal:
    #             nombre_bodega_secundario=self.env['stock.warehouse'].search([('name','=',i.stock_location_name)],limit=1).lot_stock_id.id
    #             picking_line.append(
    #                         (0, 0, {
    #                             "product_id": i.product_id.id,
    #                             "product_uom_qty":i.qty,
    #                             "location_dest_id": config_location_id,
    #                             "location_id": nombre_bodega_secundario,
    #                             "product_uom":i.product_id.product_tmpl_id.uom_id.id,
    #                             "name":i.product_id.product_tmpl_id.name,   
    #                         }))
    #     if picking_line:
    #         picking_ids=[]
    #         picking={
    #             'partner_id':order_id.company_id.partner_id.id,
    #             "location_dest_id": config_location_id,
    #             "location_id": nombre_bodega_secundario,
    #             'origin':order_id.name,
    #             'move_ids_without_package':picking_line,
    #             'picking_type_id':5
    #         }
    #         pickng_creado=model_stock_picking.create(picking)
    #         pickng_confirmado=pickng_creado.action_confirm()

    #         picking_ids.append(pickng_creado.id)
    #         order_id.write(
    #             {
    #                 "picking_ids": [(4,pickng_creado.id)]
    #             }
    #         )
    #         return order_id




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

    @api.model
    def _calculo_precios_venta(self):
        productos=self.env['product.template'].search([('producto_margen','!=',0)])
        for p in productos:
            margen=1+(p.producto_margen/100)
            p.list_price=round((p.standard_price*margen)*1.19,0)
            # print(margen)
            # print(p.standard_price)
            # print(p.list_price)
    