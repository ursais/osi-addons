# Import Odoo Libs
from odoo import api, models


class StockMove(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "stock.move"

    # METHODS #####

    @api.model_create_multi
    def create(self, vals_list):
        stock_moves = super().create(vals_list)
        for values in vals_list:
            mo_id = values.get("raw_material_production_id", False) or values.get(
                "production_id", False
            )
            if mo_id:
                production_order = self.env["mrp.production"].browse(mo_id)
                sale_order_id = production_order.sale_order_id
                is_constrained_product_moves = (
                    production_order.picking_ids.move_ids_without_package.filtered(
                        lambda l: l.state not in ["done", "cancel"]
                        and l.product_id.is_constrained
                    )
                )
                if (
                    production_order
                    and sale_order_id
                    and sale_order_id.date_confirm
                    and is_constrained_product_moves
                ):
                    for move in is_constrained_product_moves:
                        move.date = sale_order_id.date_confirm
        return stock_moves

    # END #########
