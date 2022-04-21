# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    sales_hold = fields.Boolean(
        string="Sales Hold",
        default=False,
        help="If checked, new quotations cannot be confirmed",
    )
    credit_limit = fields.Monetary(string="Credit Limit")
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

    def write(self, vals):

        res = super(Partner, self).write(vals)

        if "credit_limit" in vals:
            domain = [("ship_hold", "=", True)]
            for partner in self:
                is_credit_limit = False
                if self.env.company.is_company_credit_limit:
                    domain.append(
                        ("partner_id", "child_of", partner.parent_id.id or partner.id)
                    )
                    if partner.parent_id and partner.parent_id.credit_limit > 0:
                        is_credit_limit = True
                    elif partner.credit_limit > 0:
                        is_credit_limit = True
                else:
                    domain.append(("partner_id", "=", partner.id))
                    if self.credit_limit > 0:
                        is_credit_limit = True
                order_ids = self.env["sale.order"].search(domain)
                if is_credit_limit and order_ids:
                    if not self.check_limit(order_ids[0]):
                        order_ids.write({"ship_hold": False})
        return res

    def check_limit(self, sale_id):
        partner_id = sale_id.partner_id
        # Other orders for this partner
        domain = []
        if self.env.company.is_company_credit_limit:
            domain.append(
                ("partner_id", "child_of", partner_id.parent_id.id or partner_id.id)
            )
        else:
            domain.append(("partner_id", "=", partner_id.id))
        order_ids = self.env["sale.order"].search(
            domain
            + [
                ("state", "=", "sale"),
                ("invoice_status", "!=", "invoiced"),
            ]
        )
        # Open invoices (unpaid or partially paid invoices --
        # It is already included in partner.credit
        invoice_ids = self.env["account.move"].search(
            domain
            + [
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
                        or invoice.invoice_date
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
        partner_id = sale_id.partner_id
        if self.env.company.is_company_credit_limit:
            partner_id = sale_id.partner_id.parent_id or sale_id.partner_id
        if (
            partner_id.credit_limit
            and (existing_invoice_balance + existing_order_balance)
            > partner_id.credit_limit
        ):
            return True
        else:
            return False
