# Import Odoo libs
from odoo import fields, models


class StockPicking(models.Model):
    """
    Adding fields to Stock Picking.
    """

    _inherit = "stock.picking"

    # COLUMNS ##########

    rush_order = fields.Boolean("Rush Order", related="sale_id.rush_order")

    # END ##########
