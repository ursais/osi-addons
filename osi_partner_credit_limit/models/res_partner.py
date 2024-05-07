# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import fields, models

import logging
logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    sales_hold = fields.Boolean(
        string="Sales Hold",
        default=False,
        help="If checked, new quotations cannot be confirmed",
    )
    grace_period = fields.Integer(
        string="Grace Period",
        help="Grace period added on top of the customer \
        payment term "
        "(in days)",
    )
    credit_hold = fields.Boolean(
        string="Credit Hold",
        help="Place the customer on credit hold to prevent \
            from shipping goods",
    )
    credit_used = fields.Monetary(string="Credit Used", compute="calculate_credit")
    credit_available = fields.Monetary(
        string="Credit Available", compute="calculate_credit"
    )
    ship_hold_days = fields.Integer(
        string="Customer Credit Period",
        help="Period past scheduled date for customer hold to verify credit card authorization",
    )
    def get_existing_invoice_balance(self, partner_id):
        # Open invoices (unpaid or partially paid invoices --
        # It is already included in partner.credit
        invoice_ids = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id.id),
                # ('state', '=', 'draft'),
                ("state", "in", ["open", "posted"]),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("move_type", "in", ["out_invoice", "out_refund"]),
            ]
        )
        # Invoices that are open (also shows up as part of partner.
        # Credit, so must be deducted
        now = fields.Datetime.to_string(datetime.now())
        grace_period = timedelta(days=partner_id.grace_period)
        existing_invoice_balance = sum(
            invoice_ids.filtered(
                lambda inv: (
                    inv.invoice_date_due
                    or inv.date_invoice
                    or inv.create_date + grace_period > now
                )
            ).mapped("amount_residual")
        )

        return existing_invoice_balance

    def get_existing_order_balance(self, partner_id):
        # Other orders for this partner
        order_ids = self.env["sale.order"].search(
            [
                ("partner_id", "=", partner_id.id),
                ("state", "=", "sale"),
                ("invoice_status", "!=", "invoiced"),
            ]
        )

        # Confirmed orders - invoiced - draft or open / not invoiced
        existing_order_balance = sum(order_ids.mapped("amount_total"))

        return existing_order_balance


    def calculate_credit(self):
        for partner_id in self:
            existing_order_balance = self.get_existing_order_balance(partner_id)
            existing_invoice_balance = self.get_existing_invoice_balance(partner_id)

            # All open sale orders + partner credit (AR balance) -
            # Open invoices (already included in partner credit)
            partner_id.credit_used = existing_invoice_balance + existing_order_balance
            partner_id.credit_available = (
                partner_id.credit_limit - partner_id.credit_used
            )
    def write(self, vals):
        res = super(Partner, self).write(vals)
        if "credit_limit" or "credit_hold" in vals:
            for partner in self:
                order_ids = self.env["sale.order"].search(
                    [("partner_id", "=", partner.id)]
                )
                # only if partner is on credit hold, set sale orders on ship hold immediately
                ship_hold = partner.credit_hold

                # check for credit_limit
                if partner.credit_limit > 0 and order_ids:
                    if not ship_hold and not self.check_limit(order_ids[0]):
                        ship_hold = False
                    else:
                        ship_hold = True

                order_ids.write({"ship_hold": ship_hold})

        # user reset credit authorization days
        if "ship_hold_days" in vals:
            pickings = self.env["stock.picking"].search(
                [
                    ("picking_type_code", "=", "outgoing"),
                    ("partner_id.parent_id", "=", self.id),
                    ("state", "in", ("assigned", "confirmed", "waiting")),
                ]
            )
            pickings.compute_customer_hold()

        return res

    def check_limit(self, sale_id):
        partner_id = sale_id.partner_id
        # Confirmed orders - invoiced - draft or open / not invoiced
        existing_order_balance = self.get_existing_order_balance(partner_id)
        existing_invoice_balance = self.get_existing_invoice_balance(partner_id)

        # All open sale orders + partner credit (AR balance) -
        # Open invoices (already included in partner credit)
        if (
            partner_id.credit_limit
            and (existing_invoice_balance + existing_order_balance)
            > partner_id.credit_limit
        ):
            return True
        else:
            return False
