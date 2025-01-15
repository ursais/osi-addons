# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Inherit the Product Variant Object Adding Fields and Methods
    """

    _inherit = "product.template"

    # COLUMNS ##########

    default_code = fields.Char("Internal Reference", compute="", inverse="", store=True)

    # END ##########
