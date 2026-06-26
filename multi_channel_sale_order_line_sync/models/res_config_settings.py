# Copyright (C) 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mc_append_lines_to_confirmed = fields.Boolean(
        string="Append New Channel Lines to Confirmed Orders",
        default=True,
        config_parameter="multi_channel_sale_order_line_sync.append_to_confirmed",
        help="When a channel order is updated after confirmation (e.g. by "
        "post-purchase upsell apps), append any new line items to the existing "
        "confirmed Sales Order instead of skipping them.",
    )
