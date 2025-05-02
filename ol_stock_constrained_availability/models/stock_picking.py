# Import Odoo Libs
from odoo import models


class StockPicking(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "stock.picking"

    # METHODS #####

    def write(self, vals):
        res = super().write(vals)
        if "scheduled_date" in vals or vals.get("scheduled_date"):
            stock_moves = self.move_ids_without_package.filtered(
                lambda l: l.state not in ["done", "cancel"]
            )
            for stock_move in stock_moves:
                if stock_move.product_id.is_constrained and stock_move.sale_line_id:
                    stock_move.date = stock_move.sale_line_id.order_id.date_confirm
        return res

    # END #########
