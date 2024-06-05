from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    audi_product_ref = fields.Char(string="Product Reference")

