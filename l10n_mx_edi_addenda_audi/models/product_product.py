from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    audi_product_ref = fields.Char(related="product_variant_id")
