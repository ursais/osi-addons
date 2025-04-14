# Import Odoo Libs
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    Updates to product variants to support configurations
    """

    _inherit = "product.product"

    # COLUMNS #####

    bom_line_ids = fields.One2many(
        comodel_name="mrp.bom.line",
        inverse_name="product_id",
        string="BoM Lines",
    )

    # END #########
    # METHODS #####