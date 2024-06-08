from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    vw_ref = fields.Char(string="VW Reference")
