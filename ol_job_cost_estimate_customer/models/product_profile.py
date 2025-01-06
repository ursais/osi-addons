# Import Odoo libs
from odoo import fields, models


class ProductProfile(models.Model):
    """
    Inherit Product Profiles for updating the detailed_type selection field.
    """

    _inherit = "product.profile"

    # COLUMNS ##########

    detailed_type = fields.Selection(
        selection_add=[("product", "Storable Product")],
        ondelete={"product": "cascade"},
    )

    # END #########
