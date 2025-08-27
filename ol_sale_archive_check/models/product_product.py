# Import Odoo libs
from odoo import models


class ProductProduct(models.Model):
    """
    Add methods to trigger check archive on sale orders.
    """

    _inherit = "product.product"

    # METHODS #########

    def write(self, vals):
        was_active = {p.id: p.active for p in self}
        res = super().write(vals)

        # Only check if bom is being archived.
        if "active" in vals and vals["active"] is False:
            # Only trigger for ones that were previously active
            archived_products = self.filtered(lambda p: was_active.get(p.id))
            if archived_products:
                # Run archive check using job queue
                self.with_delay()._trigger_sale_order_archive_check(archived_products)

        return res

    def _trigger_sale_order_archive_check(self, products):
        complete_substate = self.env.ref("ol_sale_substate.base_substate__complete")

        SaleOrder = self.env["sale.order"]

        # 1. Orders where product_id is directly archived
        direct_orders = SaleOrder.search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.product_id", "in", products.ids),
            ]
        )

        # 2. Orders where bom_id contains one of the archived products as a component
        bom_lines = self.env["mrp.bom.line"].search(
            [("product_id", "in", products.ids)]
        )
        bom_ids = bom_lines.mapped("bom_id").ids

        bom_orders = SaleOrder.search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.bom_id", "in", bom_ids),
            ]
        )

        # Merge both sets (duplicates auto-handled by Odoo)
        sale_orders = direct_orders | bom_orders

        for order in sale_orders:
            # Log chatter message for archive status change
            order._log_archive_status_changes(order)
            # Now check for exception
            order.sale_check_exception()

    # END #########
