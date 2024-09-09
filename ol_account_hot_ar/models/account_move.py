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
                invoice.hot_ar = True

    @api.model
    def _update_hot_ar_invoices_cron(self):
        # Find all open customer invoices that haven't been paid yet
        # Use sudo to get ALL invoices for ALL companies
        invoices = self.sudo().search(
            [
                (
                    "move_type",
                    "in",
                    ("out_invoice", "in_invoice", "out_refund", "in_refund"),
                ),
                ("state", "=", "posted"),
                ("payment_state", "not in", ("in_payment", "paid", "reversed")),
                ("invoice_date_due", "!=", False),
                ("hot_ar", "=", False),
                ("override_hot_ar", "=", False),
                ("company_id.hot_ar_grace_period", ">", 0),
            ]
        )

        today = fields.Date.today()

        for invoice in invoices:
            # Check if the invoice is past the grace period
            if (
                invoice.invoice_date_due
                + timedelta(days=invoice.company_id.hot_ar_grace_period)
                < today
            ):
                invoice.hot_ar = True

    # END #########
