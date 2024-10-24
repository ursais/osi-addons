# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api


class StockPicking(models.Model):
    """
    Add webhook compatibility to stock picking records
    """

    _name = "stock.picking"
    _inherit = ["stock.picking", "webhook.mixin"]

    def trigger_delivery_order_webhook(self):
        """
        Filter out any stock pickings that aren't deliveries for sale orders,
        then trigger the webhook
        """
        delivery_orders = self.filtered(
            lambda p: p.picking_type_code == "outgoing" and p.sale_id
        )
        webhook_event = self.env.ref("ol_webhooks.stock_picking_tracking_info_update")
        webhook_event.trigger(records=delivery_orders, operation_override="update")
