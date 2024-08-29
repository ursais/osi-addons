# Import Odoo Libs
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add Blind Dropship product to settings"""

    _inherit = "res.config.settings"

    # COLUMNS #####

    blind_drop_ship_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Blind Drop Ship Product",
        config_parameter="stock_move.blind_drop_ship",
        help="Product to indicate blind drop shipping",
    )

    # END #########
