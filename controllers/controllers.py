# -*- coding: utf-8 -*-
from odoo import http

# class MethodRielec(http.Controller):
#     @http.route('/method_rielec/method_rielec/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/method_rielec/method_rielec/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('method_rielec.listing', {
#             'root': '/method_rielec/method_rielec',
#             'objects': http.request.env['method_rielec.method_rielec'].search([]),
#         })

#     @http.route('/method_rielec/method_rielec/objects/<model("method_rielec.method_rielec"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('method_rielec.object', {
#             'object': obj
#         })