# Import Odoo libs
from odoo import api, models


class SaleOrder(models.Model):
    """Add method to compute the sale substate changes."""

    _inherit = "sale.order"

    # METHODS #####

    def update_substate(self):
        quot_sent_substate = self.env.ref(
            "ol_sale_substate.base_substate__quot_sent", raise_if_not_found=False
        )
        order_review_substate = self.env.ref(
            "ol_sale_substate.base_substate__order_review", raise_if_not_found=False
        )
        production_substate = self.env.ref(
            "ol_sale_substate.base_substate__production", raise_if_not_found=False
        )
        waiting_substate = self.env.ref(
            "ol_sale_substate.base_substate__waiting", raise_if_not_found=False
        )
        shipped_substate = self.env.ref(
            "ol_sale_substate.base_substate__shipped", raise_if_not_found=False
        )
        complete_substate = self.env.ref(
            "ol_sale_substate.base_substate__complete", raise_if_not_found=False
        )

        for order in self:
            # --- Quotation state ---
            if order.state == "sent":
                active_exceptions = order.exception_ids.filtered(lambda e: e.active)
                if active_exceptions and not order.ignore_exception:
                    if (
                        order_review_substate
                        and order.substate_id != order_review_substate
                    ):
                        order.write({"substate_id": order_review_substate.id})
                    continue
                elif (
                    quot_sent_substate
                    and not active_exceptions
                    and order.substate_id != order_review_substate
                ):
                    order.write({"substate_id": quot_sent_substate.id})
                    continue

            # --- Sale state ---
            elif order.state == "sale":
                new_substate = None

                # Stock lines
                stock_lines = order.order_line.filtered(
                    lambda l: not l.display_type
                    and l.product_id.type in ("product", "consu")
                )

                # --- Production / Waiting ---
                if order.mrp_production_ids:
                    has_active_mo = any(
                        mo.is_planned
                        or mo.state in ("progress", "to_close")
                        or (
                            not mo.workorder_ids
                            and mo.state not in ("done", "draft", "cancel")
                        )
                        for mo in order.mrp_production_ids
                    )
                    new_substate = (
                        production_substate if has_active_mo else waiting_substate
                    )

                # --- Shipped (overrides production/waiting if stock delivered) ---
                if stock_lines and all(
                    line.qty_delivered >= line.product_uom_qty for line in stock_lines
                ):
                    new_substate = shipped_substate

                # --- Complete logic ---
                # Only posted final invoices (non-downpayment) count
                final_invoices = order.invoice_ids.filtered(
                    lambda inv: inv.state == "posted"
                    and any(not line.is_downpayment for line in inv.invoice_line_ids)
                )

                # Fully paid if at least one posted final invoice exists and all such invoices are in payment or paid
                fully_paid = bool(final_invoices) and all(
                    inv.payment_state in ("in_payment", "paid")
                    for inv in final_invoices
                )

                # Fully delivered (true for service-only orders)
                fully_delivered = (
                    all(
                        line.qty_delivered >= line.product_uom_qty
                        for line in stock_lines
                    )
                    if stock_lines
                    else True
                )

                # Only mark complete if both conditions met
                if fully_paid and fully_delivered:
                    new_substate = complete_substate

                # Apply substate if changed
                if new_substate and order.substate_id != new_substate:
                    order.write({"substate_id": new_substate.id})

            # --- Detect exceptions ---
            order.detect_exceptions()

    @api.depends("invoice_ids.payment_state")
    def _compute_update_substate(self):
        for order in self:
            order.update_substate()

    def action_lock(self):
        """Trigger a substate check if Lock is pressed"""
        res = super().action_lock()
        self.update_substate()
        return res

    def write(self, vals):
        res = super().write(vals)

        # Only run substate logic if something relevant changed
        if any(f in vals for f in ("exception_ids", "ignore_exception", "state")):
            # Only update substates for "sent" orders
            sent_orders = self.filtered(lambda o: o.state == "sent")
            if sent_orders:
                sent_orders.update_substate()

        return res

    @api.model_create_multi
    def create(self, vals):
        orders = super().create(vals)
        orders.update_substate()
        return orders

    # END #####
