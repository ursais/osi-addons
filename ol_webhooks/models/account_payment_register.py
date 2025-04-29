# Import Python libs

# Import Odoo libs
from odoo import models


class AccountPaymentRegister(models.TransientModel):

    _inherit = "account.payment.register"

    def _reconcile_payments(self, to_process, edit_mode=False):
        """
        This function is called if payments are applied to invoices
        if any of these events happens we want to trigger webhooks for these invoices
        """
        res = super()._reconcile_payments(to_process, edit_mode)
        # Trigger a webhook for the invoice
        moves = self.line_ids.mapped("move_id")
        moves.trigger_webhook()
        # Make sure that all related customer record updates are also broadcasted
        moves.mapped("partner_id").trigger_webhooks_for_related()
        return res
