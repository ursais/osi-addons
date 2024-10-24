# Import Python libs

# Import Odoo libs
from odoo import models


class AccountMove(models.Model):
    """
    Add webhook compatibility to Invoices
    """

    _inherit = "account.payment"

    def _post_payment_post_actions(self):
        """
        This function is called if a Payment is registered for one or multiple invoices
        if any of these events happens we want to trigger webhooks for these invoices
        """
        res = super()._post_payment_post_actions()
        invoices = self.mapped("invoice_ids")
        invoices.trigger_webhook()
        # Make sure that all related customer record updates are also broadcasted
        invoices.mapped("partner_id").trigger_webhooks_for_related()
        return res
