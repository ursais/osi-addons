# Import Odoo Libs
from odoo import fields, models


class ResPartner(models.Model):
    """
    Extend res.partner to add override_company_name field.
    This field allows overriding the company name display for child partners.
    """

    _inherit = "res.partner"

    # COLUMNS #####

    override_company_name = fields.Char(
        string="Override Company Name",
        help="Override the company name for this contact. "
        "This is useful for delivery addresses where a different company name should be displayed.",
    )

    # END #########
