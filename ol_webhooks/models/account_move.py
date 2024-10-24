# Import Python libs

# Import Odoo libs
from odoo import models


class AccountMove(models.Model):
    """
    Add webhook compatibility to Invoices
    """

    _name = "account.move"
    _inherit = ["account.move", "webhook.mixin"]

    @staticmethod
    def get_webhook_trigger_computed_models():
        """
        We want to potentionaly trigger webhooks if related values for any of these object are written
        """
        return ["sale.order", "res.partner"]

    def post(self):
        """
        Posting an invoice updates a lot of financial data that other system have interest in.
        We need to make sure that all related records are updated.
        """
        res = super().post()

        for move in self:
            if move.type not in ("out_invoice"):
                # Filter out any account_moves that are not out_invoices
                continue
            move.partner_id.trigger_webhooks_for_related()
        return res

    def _reconcile_payment_allocation_event(self, payments, total_amount_applied):
        """
        This function is called if payments are applied to invoices
        if any of these events happens we want to trigger webhooks for these invoices
        """
        res = super()._reconcile_payment_allocation_event(
            payments, total_amount_applied
        )
        self.trigger_webhook()
        # Make sure that all related customer record updates are also broadcasted
        self.mapped("partner_id").trigger_webhooks_for_related()
        return res

    def _create_filter(self, values):
        """
        Any filtering logic that needs to happen before we want to trigger webhooks
        """

        account_moves = super()._create_filter(values)
        return account_moves.webhook_filter()

    def _update_filter(self, values):
        """
        Any filtering logic that needs to happen before we want to trigger webhooks
        """

        account_moves = super()._update_filter(values)

        # Filter out any draft states, as we don't want to send update webhook events for those
        return account_moves.webhook_filter().filtered(
            lambda move: move.state not in ("draft")
        )

    def webhook_filter(self):
        """
        Filter out any account_moves that are not out_invoices
        """
        return self.filtered(lambda move: move.type in ["out_invoice"])
