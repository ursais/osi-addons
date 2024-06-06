from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    audi_ref = fields.Char(related="product_tmpl_id.audi_ref")
