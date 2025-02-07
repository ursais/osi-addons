from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit Settings to add default delay/prepare values."""

    _inherit = "res.config.settings"

    # COLUMNS #########

    produce_delay = fields.Integer(
        string="Default - Manufacturing Lead Time",
        config_parameter="mrp_batch.default_produce_delay",
        default=4,
    )
    days_to_prepare_mo = fields.Integer(
        string="Default - Days to Prepare",
        config_parameter="mrp_batch.default_days_to_prepare_mo",
        default=1,
    )
    mo_batch_mode = fields.Selection(
        [
            (
                "single",
                "Single Batch for ALL Manufacturing Orders on Sale Order Confirmation",
            ),
            (
                "multiple",
                "Separate Batch for EACH Manufacturing Orders on Sale Order Confirmation",
            ),
        ],
        string="MO Batch Mode",
        config_parameter="mrp_batch.batch_mode",
        default="single",
    )

    # END #########
