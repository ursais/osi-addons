from odoo import _, fields, models
from odoo.addons.ol_product.models.product_template import SYSTEM_TIERS


class ProductConfigurator(models.TransientModel):
    _inherit = "product.configurator"

    # COLUMNS #####
    system_tier = fields.Selection(
        selection=SYSTEM_TIERS,
        string="Type of System",
        default="normal",
        required=True,
        help="Select the type of system you want to create.",
    )
    # END #########
