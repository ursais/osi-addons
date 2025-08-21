# Import Odoo libs
from odoo import models


class MrpBom(models.Model):
    """
    Add methods to trigger check archive on sale orders.
    """

    _inherit = "mrp.bom"

    # METHODS #########

    def write(self, vals):
        was_active = {b.id: b.active for b in self}
        res = super().write(vals)

        # Only check if bom is being archived.
        if "active" in vals and vals["active"] is False:
            archived_boms = self.filtered(lambda b: was_active.get(b.id))
            if archived_boms:
                # Run archive check using job queue
                self.with_delay()._trigger_sale_order_archive_check(archived_boms)
        return res

    def _trigger_sale_order_archive_check(self, boms):
        # Filter out BOMs whose product is already archived since the check would
        # trigger on archiving of product too and we don't want duplicate message
        active_boms = boms.filtered(lambda b: b.product_id and b.product_id.active)
        if not active_boms:
            return  # Nothing to check

        complete_substate = self.env.ref("ol_sale_substate.base_substate__complete")
        sale_orders = self.env["sale.order"].search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.bom_id", "in", boms.ids),
            ]
        )
        for order in sale_orders:
            # Log chatter message for archive status change
            order._log_archive_status_changes(order)
            # Now check for exception
            order.sale_check_exception()

    # END #########
