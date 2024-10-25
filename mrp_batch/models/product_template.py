from odoo import models, fields, api

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    is_allowe_split_mo = fields.Boolean(string='Allowe Split Mo',default=True)
    