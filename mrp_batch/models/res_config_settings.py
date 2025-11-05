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
                "multiple",
                "Separate Batch for EACH Manufacturing Order on Sale Order Confirmation",
            ),
            (
                "single",
                "Single Batch for ALL Manufacturing Orders on Sale Order Confirmation",
            ),
        ],
        string="MO Batch Mode",
        config_parameter="mrp_batch.batch_mode",
        default="multiple",
    )
    enable_delay_action_assign = fields.Boolean(
        string="Enable Queuing Action Assign",
        config_parameter="mrp_batch.enable_delay_action_assign",
    )
    enable_delay_action_confirm = fields.Boolean(
        string="Enable Queuing Action Confirm",
        config_parameter="mrp_batch.enable_delay_action_confirm",
    )
    enable_delay_button_plan = fields.Boolean(
        string="Enable Queuing Button Plan",
        config_parameter="mrp_batch.enable_delay_button_plan",
    )
    enable_delay_button_unplan = fields.Boolean(
        string="Enable Queuing Button Unplan",
        config_parameter="mrp_batch.enable_delay_button_unplan",
    )
    enable_delay_action_unreserve = fields.Boolean(
        string="Enable Queuing Action Unreserve",
        config_parameter="mrp_batch.enable_delay_action_unreserve",
    )
    enable_delay_action_done = fields.Boolean(
        string="Enable Queuing Action Done",
        config_parameter="mrp_batch.enable_delay_action_done",
    )
    enable_delay_action_cancel = fields.Boolean(
        string="Enable Queuing Action Cancel",
        config_parameter="mrp_batch.enable_delay_action_cancel",
    )
    enable_delay_component_availability = fields.Boolean(
        string="Enable Queuing Component Availability",
        config_parameter="mrp_batch.enable_delay_component_availability",
    )
    enable_delay_component_availability_details = fields.Boolean(
        string="Enable Queuing Component Availability Details",
        config_parameter="mrp_batch.enable_delay_component_availability_details",
    )
    enable_delay_so_action_confirm = fields.Boolean(
        string="Enable Queuing on Sale order confirm",
        config_parameter="mrp_batch.enable_delay_so_action_confirm",
    )
    use_batch_transfer = fields.Boolean(
        string="Use Batch Transfers",
        config_parameter="mrp_batch.use_batch_transfer",
    )

    # END #########
