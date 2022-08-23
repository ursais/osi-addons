# -*- coding: utf-8 -*-
# from odoo import http


# class Osi-loans(http.Controller):
#     @http.route('/osi-loans/osi-loans', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/osi-loans/osi-loans/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('osi-loans.listing', {
#             'root': '/osi-loans/osi-loans',
#             'objects': http.request.env['osi-loans.osi-loans'].search([]),
#         })

#     @http.route('/osi-loans/osi-loans/objects/<model("osi-loans.osi-loans"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('osi-loans.object', {
#             'object': obj
#         })
