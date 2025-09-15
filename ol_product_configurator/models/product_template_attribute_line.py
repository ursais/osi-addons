# Import Odoo libs
from odoo import fields, models


class ProductTemplateAttributeLine(models.Model):
    """
    Inherit the Product Template Attribute Line Object Adding Fields and methods
    """

    _inherit = "product.template.attribute.line"

    # COLUMNS ##########

    default_val = fields.Many2one(
        comodel_name="product.attribute.value", company_dependent=True
    )

    # END ##########
