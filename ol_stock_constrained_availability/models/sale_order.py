# Import Odoo Libs
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "sale.order"

    # FIELDS #####
    date_confirm = fields.Date(string="Confirmation Date", readonly="1", copy=False)
    # END #####

    # METHODS #####
    def action_confirm(self):
        # Calls the original `action_confirm` method from the super class to
        # confirm the record.
        res = super().action_confirm()
        self.date_confirm = fields.Date.context_today(self)
        stock_moves = self.env["stock.move"].search(
            [
                ("sale_line_id", "in", self.order_line.ids),
                ("state", "not in", ["done", "cancel"]),
            ]
        )
        for stock_move in stock_moves:
            if stock_move.product_id.is_constrained:
                stock_move.date = self.date_confirm
                if len(stock_moves) > 1:
                    stock_move.picking_id.scheduled_date = self.date_confirm
        return res

    # END #####
