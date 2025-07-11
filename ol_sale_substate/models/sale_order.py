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
        complete_substate = self.env.ref(
            "ol_sale_substate.base_substate__complete", raise_if_not_found=False
        )

        for order in self:
            # Only apply these rules if order is in 'sent' or 'sale' state
            if order.state == "sent":
                # Set substate to review if there are exceptions
                active_exceptions = order.exception_ids.filtered(lambda e: e.active)
                if active_exceptions and not order.ignore_exception:
                    if (
                        order_review_substate
                        and order.substate_id != order_review_substate
                    ):
                        order.write({"substate_id": order_review_substate.id})
                elif (
                    quot_sent_substate
                    and order.substate_id != quot_sent_substate
                    and not active_exceptions
                ):
                    order.write({"substate_id": quot_sent_substate.id})

            elif order.state == "sale":
                new_substate = None

                if order.mrp_production_ids:
                    # Determine if any MOs are planned or started
                    has_active_mo = any(
                        mo.is_planned
                        or mo.state in ("progress", "to_close")
                        or (
                            not mo.workorder_ids
                            and mo.state not in ("done", "draft", "cancel")
                        )
                        for mo in order.mrp_production_ids
                    )
                    # Set to in production if any mo is planned or started
                    if production_substate and has_active_mo:
                        new_substate = production_substate
                    # Otherwise set to waiting
                    elif waiting_substate:
                        new_substate = waiting_substate

                if order.picking_ids:
                    # Determine if fully delivered
                    all_delivered = all(
                        line.qty_delivered >= line.product_uom_qty
                        for line in order.order_line
                        if not line.display_type
                        and line.product_id.type in ("product", "consu")
                    )
                    # Set to complete if fully delivered
                    if all_delivered and order.substate_id != complete_substate:
                        new_substate = complete_substate

                if new_substate and order.substate_id != new_substate:
                    order.write({"substate_id": new_substate.id})

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
