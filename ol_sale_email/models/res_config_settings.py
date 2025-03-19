# Import Odoo libs
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit Settings to add backorder email functionality setting."""

    _inherit = "res.config.settings"

    # COLUMNS #########

    enable_backorder_email = fields.Boolean(
        string="Enable Backorder Email",
        config_parameter="sale.enable_backorder_email",
        default=False,
        help="Enable backorder emails when Sale Order is confirmed.",
    )
    # END #########
