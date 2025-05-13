# Import Odoo Libs
from odoo import api,models


class MRPProduction(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "mrp.production"

    # METHODS #####

    def action_confirm(self):
        result = super().action_confirm()
        stock_moves = self.move_raw_ids.filtered(
            lambda l: l.state not in ["done", "cancel"]
        )
        for stock_move in stock_moves:
            if stock_move.product_id.is_constrained and self.sale_order_id.date_confirm:
                stock_move.date = self.sale_order_id.date_confirm
        return result


    @api.model_create_multi
    def create(self, vals_list):
        production_orders = super().create(vals_list)
        for production in production_orders:
            if production.sale_order_id and production.sale_order_id.date_confirm:
                for move in production.move_raw_ids:
                    if move.product_id.is_constrained:
                        move.date = production.sale_order_id.date_confirm
        return production_orders

    def write(self, vals):
        res = super().write(vals)
        for production in self:
            if production.sale_order_id and production.sale_order_id.date_confirm:
                for move in production.move_raw_ids:
                    if move.product_id.is_constrained:
                        move.date = production.sale_order_id.date_confirm
        return res

    # END #########
