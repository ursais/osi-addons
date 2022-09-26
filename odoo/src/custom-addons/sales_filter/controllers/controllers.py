# -*- coding: utf-8 -*-
# from odoo import http


# class SalesFilter(http.Controller):
#     @http.route('/sales_filter/sales_filter', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_filter/sales_filter/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_filter.listing', {
#             'root': '/sales_filter/sales_filter',
#             'objects': http.request.env['sales_filter.sales_filter'].search([]),
#         })

#     @http.route('/sales_filter/sales_filter/objects/<model("sales_filter.sales_filter"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_filter.object', {
#             'object': obj
#         })
