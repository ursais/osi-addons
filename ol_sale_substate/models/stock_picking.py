# Import Odoo libs
from odoo import models


class StockPicking(models.Model):
    """Add method to compute the sale substate change for stock pickings."""

    _inherit = "stock.picking"

    # METHODS #####

    def button_validate(self):
        """Trigger the update substate method during confirmation"""
        res = super().button_validate()

        for picking in self:
            # Only want to do substate for delivery orders
            if picking.picking_type_code != "outgoing":
                continue

            # Get sale order and do nothing if not found
            sale_orders = picking.sale_id or picking.group_id.sale_id
            if not sale_orders:
                continue

            # Run the substate check on those orders
            for order in sale_orders:
                order.update_substate()

        return res

    # END #####
