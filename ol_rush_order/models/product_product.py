# Import Odoo libs
from odoo import fields, models


class ProductProduct(models.Model):
    """
    Adding fields to Product Variant.
    """

    _inherit = "product.product"

    # COLUMNS ##########

    triggers_rush = fields.Boolean("Triggers Rush")

    # END ##########
