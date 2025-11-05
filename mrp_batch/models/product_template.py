# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit Product Template add MO Split Configuration Field."""

    _inherit = "product.template"

    # COLUMNS #########

    is_allow_split_mo = fields.Boolean(
        string="Allow Split Mo",
        default=True,
    )

    # END #########
