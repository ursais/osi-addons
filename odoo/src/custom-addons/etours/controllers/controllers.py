# -*- coding: utf-8 -*-
# from odoo import http


# class Etours(http.Controller):
#     @http.route('/etours/etours', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/etours/etours/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('etours.listing', {
#             'root': '/etours/etours',
#             'objects': http.request.env['etours.etours'].search([]),
#         })

#     @http.route('/etours/etours/objects/<model("etours.etours"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('etours.object', {
#             'object': obj
#         })
