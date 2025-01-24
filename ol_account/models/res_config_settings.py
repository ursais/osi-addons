# Import Odoo libs
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Inherit settings to add the fields related to auto invoice creation.
    """

    _inherit = "res.config.settings"

    # COLUMNS ######

    auto_create_invoice_delivery_validate = fields.Boolean(
        string="Auto Create invoice",
        config_parameter="ol_account.auto_create_invoice_delivery_validate",
        help="Create invoice on delivery validation.",
    )
    auto_post_invoice_delivery_validate = fields.Boolean(
        string="Auto Post invoice",
        config_parameter="ol_account.auto_post_invoice_delivery_validate",
        help="Post invoice on delivery validation.",
    )

    # END ##########
