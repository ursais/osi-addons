# Copyright (C) 2019 - 2023, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    sales_hold = fields.Boolean(
        help="If checked, new quotations cannot be confirmed",
    )
    osi_credit_limit = fields.Monetary("Credit Limit")
    grace_period = fields.Integer(
        help="Grace period added on top of the customer payment term (in days)",
    )
    credit_hold = fields.Boolean(
        help="Place the customer on credit hold to prevent from shipping goods",
    )

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if "osi_credit_limit" or "credit_hold" in vals:
            for partner in self:
                order_ids = self.env["sale.order"].search(
                    [("partner_id", "=", partner.id)]
                )
                # only if partner is on credit hold, set sale orders on ship hold immediately
                ship_hold = partner.credit_hold

                # check for osi_credit_limit
                if partner.osi_credit_limit > 0 and order_ids:
                    if not ship_hold and not self.with_context(
                        from_sale_order=False
                    ).check_limit(order_ids[0]):
                        ship_hold = False
                    else:
                        ship_hold = True
                order_ids.write({"ship_hold": ship_hold})
        return res

    def used_credit_limit_balance(self, partner_id=None):
        # Fetch total amount of credit used by partner from open SOs and Invoices
        partner_id = partner_id or self
        order_ids = self.env["sale.order"].search(
            [
                ("partner_id", "=", partner_id.id),
                ("state", "=", "sale"),
                ("invoice_status", "!=", "invoiced"),
            ]
        )
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
        # Initialize variables
        existing_order_balance = 0.0
        existing_invoice_balance = 0.0
        # Confirmed orders - invoiced - draft or open / not invoiced
        for order in order_ids:
            existing_order_balance = existing_order_balance + order.amount_total
        # Invoices that are open (also shows up as part of partner.
        # Credit, so must be deducted
        for invoice in invoice_ids:
            if (
                fields.Datetime.to_string(
                    (
                        invoice.invoice_date_due
                        or invoice.date_invoice
                        or invoice.create_date
                    )
                    + timedelta(days=partner_id.grace_period)
                )
            ) > fields.Datetime.to_string(datetime.now()):
                continue
            else:
                existing_invoice_balance = (
                    existing_invoice_balance + invoice.amount_residual
                )
        # All open sale orders + partner credit (AR balance) -
        # Open invoices (already included in partner credit)
        return existing_order_balance + existing_invoice_balance

    def check_limit(self, sale_id=None):
        # This method will check if the Partner goes over the
        partner_id = sale_id and sale_id.partner_id or self
        if partner_id.osi_credit_limit and self.used_credit_limit_balance(partner_id) > partner_id.osi_credit_limit:
            return True
        return False
