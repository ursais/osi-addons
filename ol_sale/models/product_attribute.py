# Import Odoo libs
from odoo import fields, models


class ProductAttribute(models.Model):
    """
    Add new field to Product Attribute
    """

    _inherit = "product.attribute"

    # COLUMNS #####

    used_in_sale_description = fields.Boolean(
        string="Show in Sale Description",
        default=True,
    )

    # END #########
