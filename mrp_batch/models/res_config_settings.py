from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    produce_delay = fields.Integer(
        string="Default Manufacturing Lead Time",
        config_parameter="mrp_batch.default_produce_delay",
        default=4
    )
    days_to_prepare_mo = fields.Integer(
        string="Default Days to Prepare",
        config_parameter="mrp_batch.default_days_to_prepare_mo",
        default=1
    )
