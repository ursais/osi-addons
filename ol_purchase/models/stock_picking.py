# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """
    Adding fields,  to Stock Picking.
    """

    _inherit = "stock.picking"

    # COLUMNS ##########

    date_approve = fields.Datetime(
        string="Confirmation Date",
        related="move_ids.purchase_line_id.order_id.date_approve",
    )

    # END ##########
