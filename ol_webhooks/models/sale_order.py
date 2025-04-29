# Import Python libs

# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """
    Add webhook compatibility to Sale Orders
    """

    _name = "sale.order"
    _inherit = ["sale.order", "webhook.mixin"]

    def action_confirm(self):
        """
        Confirming sale orders updates a lot of financial data that other system have interest in.
        Make sure that all related customer record updates are also broadcasted
        """
        res = super().action_confirm()
        self.filtered(lambda so: so.state == "sale").mapped(
            "partner_id"
        ).trigger_webhooks_for_related()
        return res

    def action_lock(self):
        """
        Trigger webhooks for related partners whenever an order is locked
        """
        res = super().action_lock()
        self.mapped("partner_id").trigger_webhooks_for_related()
        return res

    def action_unlock(self):
        """
        Trigger webhooks for related partners whenever an order is unlocked
        """
        res = super().action_unlock()
        self.mapped("partner_id").trigger_webhooks_for_related()
        return res

    # TODO: (4/23/2025) Waiting for OSI to fix broken exception logic https://github.com/onlogic-enterprise/onlogic-addons/pull/158#discussion_r2056518532
    # def exceptions_updated(self):
    #     pass

    def action_webhook_test(self):
        # Trigger Webhook Update event to test webhooks
        super().action_webhook_test()

        # TODO: (4/23/2025) Waiting for OSI to finish sale booking development
        # # Also try to trigger webhooks for related Sale Bookings
        # # Get the last related Sale Booking if it exists
        # sale_bookings = self.booking_ids.sorted(key=lambda sb: sb.id, reverse=True)
        # if sale_bookings:
        #     sale_booking = sale_bookings[0]
        #     # Important! This call is made with `webhook_no_delay` so we can skip the `queue`
        #     sale_booking.with_context(webhook_no_delay=True).trigger_webhook()
