# Import Odoo Libs
from odoo import models


class MRPProduction(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "mrp.production"

    # METHODS #####
    def action_confirm(self):
        result = super().action_confirm()
        stock_moves = self.picking_ids.move_ids_without_package.filtered(
            lambda l: l.state not in ["done", "cancel"]
        )
        for stock_move in stock_moves:
            if stock_move.product_id.is_constrained:
                stock_move.date = self.sale_order_id.date_confirm
        return result

    # END #####
