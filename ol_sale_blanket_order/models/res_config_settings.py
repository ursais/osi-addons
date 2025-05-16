from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """
    Add new fields to Res Config Settings
    """

    _inherit = "res.config.settings"

    # COLUMNS #####

    blanket_order_release_days = fields.Integer(
        related="company_id.blanket_order_release_days",
        string="Days Before Scheduled Date to Release Blanket Orders",
        readonly=False,
    )

    # END #########
