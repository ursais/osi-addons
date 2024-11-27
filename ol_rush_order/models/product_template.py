from odoo import api,models,fields

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    triggers_rush = fields.Boolean("Triggers Rush")

    