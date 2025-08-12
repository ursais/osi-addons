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
        sale_orders = self.env["sale.order"].search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.product_id", "in", products.ids),
            ]
        )
        for order in sale_orders:
            # Log chatter message for archive status change
            order._log_archive_status_changes(order)
            # Now check for exception
            order.sale_check_exception()

    # END #########
