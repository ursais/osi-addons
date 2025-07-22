from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit Settings to add queuing setting for bom rebuild."""

    _inherit = "res.config.settings"

    # COLUMNS #########

    enable_delay_variant_bom_rebuild = fields.Boolean(
        string="Enable Queuing Variant BoM Rebuild",
        config_parameter="ol_mrp_bom_rebuild.enable_delay_variant_bom_rebuild",
    )

    # END #########
