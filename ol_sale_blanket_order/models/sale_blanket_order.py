# Import Odoo libs
import logging
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class SaleBlanketOrder(models.Model):
    """
    Add new fields to Sale blanket Order
    """

    _inherit = "sale.blanket.order"

    # COLUMNS #####

    auto_release = fields.Boolean()

    # END #########

    # METHODS #########

    def _prepare_so_line_vals(self, line):
        return {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.sequence,
            "price_unit": line.price_unit,
            "blanket_order_line": line.id,
            "product_uom_qty": line.remaining_uom_qty,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "customer_lead": line.customer_lead,
        }

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
    ):
        return {
            "partner_id": customer,
            "origin": self.name,
            "user_id": user_id,
            "currency_id": currency_id,
            "pricelist_id": pricelist_id,
            "payment_term_id": payment_term_id,
            "order_line": order_lines_by_customer[customer],
            "analytic_account_id": self.analytic_account_id.id,
        }

    @api.model
    def create_sale_order_cron(self):
        today = fields.Date.today()
        blanket_orders = self.search(
            [("state", "=", "open"), ("auto_release", "=", True)]
        )
        for order in blanket_orders:
            order_lines_by_customer = defaultdict(list)
            currency_id = pricelist_id = user_id = payment_term_id = 0
            for line in order.line_ids:
                if (
                    line.date_schedule
                    and (line.date_schedule + timedelta(days=line.customer_lead or 0.0))
                    <= today
                    and line.remaining_uom_qty > 0
                ):
                    vals = self._prepare_so_line_vals(line)
                    order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

                    if currency_id == 0:
                        currency_id = line.order_id.currency_id.id
                    elif currency_id != line.order_id.currency_id.id:
                        currency_id = False

                    if pricelist_id == 0:
                        pricelist_id = line.pricelist_id.id
                    elif pricelist_id != line.pricelist_id.id:
                        pricelist_id = False

                    if user_id == 0:
                        user_id = line.user_id.id
                    elif user_id != line.user_id.id:
                        user_id = False

                    if payment_term_id == 0:
                        payment_term_id = line.payment_term_id.id
                    elif payment_term_id != line.payment_term_id.id:
                        payment_term_id = False

                    if not order_lines_by_customer or not currency_id:
                        continue

                    res = []
                    for customer in order_lines_by_customer:
                        order_vals = order._prepare_so_vals(
                            customer,
                            user_id,
                            currency_id,
                            pricelist_id,
                            payment_term_id,
                            order_lines_by_customer,
                        )
                        sale_order = self.env["sale.order"].create(order_vals)
                        _logger.info(
                            _(
                                f"Created sale order: {sale_order.id}, based on blanket order: {order.id}"
                            )
                        )
                        res.append(sale_order.id)
                        sale_order.action_confirm()
                    return {
                        "domain": [("id", "in", res)],
                        "name": _("Sales Orders"),
                        "view_type": "form",
                        "view_mode": "tree,form",
                        "res_model": "sale.order",
                        "context": {"from_sale_order": True},
                        "type": "ir.actions.act_window",
                    }

    # END #########
