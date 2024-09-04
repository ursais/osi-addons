# Import Odoo Libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
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

    @api.onchange("payment_state")
    def onchange_payment_state(self):
        """When payment state changes to paid or reversed then set hot_ar to false"""
        for invoice in self:
            if invoice.payment_state in ["in_payment", "paid", "reversed"]:
                invoice.hot_ar = False

    @api.model
    def _update_hot_ar_invoices(self):
        # Find all open customer invoices that haven't been paid yet
        # Use sudo to get ALL invoices for ALL companies
        invoices = self.sudo().search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "!=", "paid"),
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
