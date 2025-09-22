# Import Odoo Libs
from odoo import api, fields, models
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR", copy=False
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
        self._check_hot_ar_and_trigger_exceptions()

    def _check_hot_ar_and_trigger_exceptions(self):
        """
        Set or unset hot_ar based on payment state and due date,
        and trigger exception logic if changed.
        """
        today = fields.Date.today()
        for invoice in self:
            old_hot_ar = invoice.hot_ar

            # If the payment state is "in_payment", "paid", or "reversed",
            # set 'hot_ar' to False.
            if invoice.payment_state in ["in_payment", "paid", "reversed"]:
                invoice.write({"hot_ar": False})

            # If the payment state is not in those values, check the due date.
            # If the invoice due date plus the company's grace period has passed,
            # set 'hot_ar' to True.
            elif (
                invoice.invoice_date_due
                and not invoice.override_hot_ar
                and invoice.invoice_date_due
                + timedelta(days=invoice.company_id.hot_ar_grace_period)
                < today
            ):
                invoice.write({"hot_ar": True})

            if old_hot_ar != invoice.hot_ar:
                sale_lines = invoice.invoice_line_ids.sale_line_ids
                sale_orders = sale_lines.mapped("order_id").filtered_domain(
                    [("state", "not in", ("cancel", "done"))]
                )

                if sale_orders:
                    sale_orders.trigger_all_exception_checks()

    @api.model
    def _update_hot_ar_invoices_cron(self):
        # Find all open customer invoices that haven't been paid yet
        # Use sudo to get ALL invoices for ALL companies
        today = fields.Date.today()
        companies = self.env["res.company"].sudo().search([])

        for company in companies:
            grace_days = company.hot_ar_grace_period
            if grace_days <= 0:
                continue

            cutoff_date = today - timedelta(days=grace_days)

            # Find overdue customer/vendor invoices that are still unpaid
            invoices = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        (
                            "move_type",
                            "in",
                            ("out_invoice", "in_invoice", "out_refund", "in_refund"),
                        ),
                        ("state", "=", "posted"),
                        ("payment_state", "not in", ("in_payment", "paid", "reversed")),
                        ("invoice_date_due", "<", cutoff_date),
                        ("invoice_date_due", "!=", False),
                        ("hot_ar", "=", False),
                        ("override_hot_ar", "=", False),
                        ("company_id", "=", company.id),
                    ]
                )
            )

            if not invoices:
                continue

            # This handles hot_ar update + exceptions
            invoices._check_hot_ar_and_trigger_exceptions()

    # END #########
