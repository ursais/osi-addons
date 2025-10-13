from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit Settings to add default delay/prepare values."""

    _inherit = "res.config.settings"

    # COLUMNS #########
    rush_lead_time = fields.Integer(
        string="Rush Lead Time",
        config_parameter="ol_sale.rush_lead_time",
        default=2,
    )