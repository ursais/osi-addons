# Import Odoo libs
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add setting to allow/disallow kit components in cost rollups."""

    _inherit = "res.config.settings"

    # COLUMNS ##########

    allowed_kit_component_cost = fields.Boolean(
        config_parameter="ol_mrp_sale_price_rollup.allowed_kit_component_cost",
        help="""This setting determines whether the cost of individual components 
        in a kit product should be considered when computing the overall cost of 
        the kit. If enabled, the cost calculation includes the sum of its components' 
        costs rather than relying solely on the kit product's cost. This impacts 
        cost tracking, inventory valuation, and possibly pricing strategies for 
        kit-based products.""",
    )

    # END #########
