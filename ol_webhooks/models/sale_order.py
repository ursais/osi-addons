# Import Python libs

# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """
    Add webhook compatibility to Sale Orders
    """

    _name = "sale.order"
    _inherit = ["sale.order", "webhook.mixin"]

    def action_confirm_pending(self):
        """
        Confirming sale orders updates a lot of financial data that other system have interest in.
        Make sure that all related customer record updates are also broadcasted
        """
        res = super().action_confirm_pending()
        self.filtered(lambda so: so.state == "sale").mapped(
            "partner_id"
        ).trigger_webhooks_for_related()
        return res

    def _post_order_edit_actions(self, order_changed):
        """
        This function is called once the Sale Order Edit is finished
        as this could update a lot of financial data that other system have interest in.
        Make sure that all related customer record updates are also broadcasted
        """
        res = super()._post_order_edit_actions(order_changed)
        if order_changed:
            self.mapped("partner_id").trigger_webhooks_for_related()
        return res

    def workflow_holds_updated(self):
        """
        This function is called if any Sale Workflow Holds are added, are resolved or unresolved
        if any of these events happens we want to trigger webhooks
        """
        self.trigger_webhook()
