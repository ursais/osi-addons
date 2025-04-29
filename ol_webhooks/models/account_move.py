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

    def action_post(self):
        """
        Posting an invoice updates a lot of financial data that other system have interest in.
        We need to make sure that all related records are updated.
        """
        res = super().action_post()

        for move in self:
            if move.move_type not in ("out_invoice"):
                # Filter out any account_moves that are not out_invoices
                continue
            move.partner_id.trigger_webhooks_for_related()
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
        return self.filtered(lambda move: move.move_type in ["out_invoice"])
