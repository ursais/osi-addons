# Import Odoo Libs
from odoo import models


class ProductProduct(models.Model):
    """
    Expose the Product template function on the Product Product
    """

    _inherit = "product.product"

    def action_webhook_test(self):
        # Trigger Webhook Update event to test webhooks
        return self.product_tmpl_id.action_webhook_test()

    def action_stock_webhook_test(self):
        # Trigger the Stock Webhook event to test webhooks
        return self.product_tmpl_id.action_stock_webhook_test()

    def action_cost_webhook_test(self):
        # Trigger the Cost Webhook event to test webhooks
        return self.product_tmpl_id.action_cost_webhook_test()

    def action_price_webhook_test(self):
        # Trigger the Price Webhook event to test webhooks
        return self.product_tmpl_id.action_price_webhook_test()

    def action_pricing_configuration_webhook_test(self):
        # Trigger the Stock Webhook event to test webhooks
        return self.product_tmpl_id.action_pricing_configuration_webhook_test()
