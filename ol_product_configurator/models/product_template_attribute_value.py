# Import Odoo libs
from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    """
    Inherit the Product Template Attribute Value Object Adding Fields and methods
    """

    _inherit = "product.template.attribute.value"

    # COLUMNS ##########

    product_id = fields.Many2one(
        "product.product",
        related="product_attribute_value_id.product_id",
    )
    company_ids = fields.Many2many(
        "res.company",
        related="product_attribute_value_id.company_ids",
    )

    # END ##########

class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
