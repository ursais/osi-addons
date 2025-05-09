# Import Odoo Libs
from odoo import api, fields, models
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
    )
    override_hot_ar = fields.Boolean(
        string="Override Hot AR",
        help="Set this to true to ignore this invoice when creating Hot AR order holds.",
        groups="account.group_account_manager",
    )

    # END #########

    # METHODS #####

    @api.depends(
        "payment_state",
        "payment_ids.state",
    )
    def _compute_payment_state(self):
        # Call the original method to ensure normal behavior is preserved.
        super(AccountMove, self)._compute_payment_state()

        # Loop through each invoice record in the current environment.
        for invoice in self:
            today = fields.Date.today()  # Get today's date.

            # If the payment state is "in_payment", "paid", or "reversed",
            # set 'hot_ar' to False.
            if invoice.payment_state in ["in_payment", "paid", "reversed"]:
                invoice.hot_ar = False
            # If the payment state is not in those values, check the due date.
            # If the invoice due date plus the company's grace period has passed,
            # set 'hot_ar' to True.
            elif (
                invoice.invoice_date_due
                + timedelta(days=invoice.company_id.hot_ar_grace_period)
                < today
            ):
                invoice.write({"hot_ar": True})

                # Trigger exception checks on the Sale Orders
                sale_orders = invoice.mapped("invoice_line_ids.sale_line_ids.order_id")
                sale_orders = sale_orders.filtered(
                    lambda so: so.state not in ("cancel", "done")
                )
                sale_lines = invoice.mapped("invoice_line_ids.sale_line_ids")
                sale_lines = sale_lines.filtered(
                    lambda sl: sl.order_id.state not in ("cancel", "done")
                )
                if sale_orders:
                    sale_orders.detect_exceptions()

                # Trigger exception checks on Manufacturing Orders
                production_orders = (
                    self.env["mrp.production"]
                    .sudo()
                    .search(
                        [
                            "|",
                            ("sale_order_line_id", "in", sale_lines.ids),
                            ("sale_order_id", "in", sale_orders.ids),
                            ("state", "not in", ("done", "cancel")),
                        ]
                    )
                )

                if production_orders:
                    production_orders.detect_exceptions()

                # Trigger exception checks on Stock Transfer
                transfers = (
                    self.env["stock.picking"]
                    .sudo()
                    .search(
                        [
                            ("sale_id", "in", sale_orders.ids),
                            ("state", "not in", ("done", "cancel")),
                        ]
                    )
                )

                if transfers:
                    transfers.detect_exceptions()

    @api.model
    def _update_hot_ar_invoices_cron(self):
        # Find all open customer invoices that haven't been paid yet
        # Use sudo to get ALL invoices for ALL companies
        today = fields.Date.today()
        companies = self.env["res.company"].sudo().search([])

        for company in companies:
            grace_days = company.hot_ar_grace_period
            if grace_days > 0:
                cutoff_date = today - timedelta(
                    days=grace_days
                )  # equivalent to timedelta

                invoices = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            (
                                "move_type",
                                "in",
                                (
                                    "out_invoice",
                                    "in_invoice",
                                    "out_refund",
                                    "in_refund",
                                ),
                            ),
                            ("state", "=", "posted"),
                            (
                                "payment_state",
                                "not in",
                                ("in_payment", "paid", "reversed"),
                            ),
                            ("invoice_date_due", "<", cutoff_date),
                            ("invoice_date_due", "!=", False),
                            ("hot_ar", "=", False),
                            ("override_hot_ar", "=", False),
                            ("company_id", "=", company.id),
                        ]
                    )
                )
                invoices.sudo().write({"hot_ar": True})

                # Trigger exception checks on the Sale Orders
                sale_orders = invoices.mapped("invoice_line_ids.sale_line_ids.order_id")
                sale_orders = sale_orders.filtered(
                    lambda so: so.state not in ("cancel", "done")
                )
                sale_lines = invoices.mapped("invoice_line_ids.sale_line_ids")
                sale_lines = sale_lines.filtered(
                    lambda sl: sl.order_id.state not in ("cancel", "done")
                )
                if sale_orders:
                    sale_orders.detect_exceptions()

                # Trigger exception checks on Manufacturing Orders
                production_orders = (
                    self.env["mrp.production"]
                    .sudo()
                    .search(
                        [
                            "|",
                            ("sale_order_line_id", "in", sale_lines.ids),
                            ("sale_order_id", "in", sale_orders.ids),
                            ("state", "not in", ("done", "cancel")),
                        ]
                    )
                )

                if production_orders:
                    production_orders.detect_exceptions()

                # Trigger exception checks on Stock Transfer
                transfers = (
                    self.env["stock.picking"]
                    .sudo()
                    .search(
                        [
                            ("sale_id", "in", sale_orders.ids),
                            ("state", "not in", ("done", "cancel")),
                        ]
                    )
                )

                if transfers:
                    transfers.detect_exceptions()

    # END #########
