# Import Odoo Libs
from odoo import fields, models


class ProductAttribute(models.Model):
    """
    Add redirect_id to attributes
    """

    _inherit = "product.attribute"

    # COLUMNS #####

    redirect_id = fields.Many2one(
        string="Redirect",
        comodel_name="product.attribute",
    )

    # END #########
