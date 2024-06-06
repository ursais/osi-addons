from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    audi_ref = fields.Char(string="Product Reference")
