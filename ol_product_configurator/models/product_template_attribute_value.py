# Import Odoo libs
from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"
    """
    Inherit the Product Template Attribute Value Object Adding Fields and methods
    """

    product_id = fields.Many2one(
        "product.product", related="product_attribute_value_id.product_id"
    )
    company_ids = fields.Many2many(
        "res.company", related="product_attribute_value_id.company_ids",
    )
