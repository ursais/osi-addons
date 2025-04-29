# Import Python libs

# Import Odoo libs
from odoo import models


class AccountPayment(models.Model):

    _inherit = "account.payment"

    def action_post(self):
        """
        This function is called if a Payment is registered for one or multiple invoices
        if any of these events happens we want to trigger webhooks for these invoices
        """
        res = super().action_post()
        # TODO: This solution is not great. This ticket will address it: https://logicsupply.atlassian.net/browse/DEV-23250
        if (
            self._context.get("active_ids")
            and self._context.get("active_model") == "account.move.line"
        ):
            moves = (
                self.env["account.move.line"]
                .browse(self._context.get("active_ids"))
                .mapped("move_id")
            )
            moves.trigger_webhook()
            # # Make sure that all related customer record updates are also broadcasted
            moves.mapped("partner_id").trigger_webhooks_for_related()
        return res
