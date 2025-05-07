# Import Odoo Libs
from odoo import api, models


class SaleOrderLine(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "sale.order.line"

    # METHODS #####

    @api.model_create_multi
    def create(self, vals_list):
        order_lines = super().create(vals_list)
        for line in order_lines:
            stock_move = self.env["stock.move"].search(
                [
                    ("sale_line_id", "=", line.id),
                    ("state", "not in", ["done", "cancel"]),
                ]
            )
            if line.product_id.is_constrained and stock_move:
                stock_move.date = line.order_id.date_confirm
        return order_lines

    def write(self, vals):
        line = super().write(vals)
        stock_move = self.env["stock.move"].search(
            [("sale_line_id", "=", self.id), ("state", "not in", ["done", "cancel"])]
        )
        if self.product_id.is_constrained and "product_uom_qty" in vals and stock_move:
            stock_move.date = self.order_id.date_confirm
        return line

    # END #########
