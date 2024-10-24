# Import Python libs
import logging

# Import Odoo libs
from odoo import models, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Add webhook compatibility to Product Template
    """

    _name = "product.template"
    _inherit = ["product.template", "webhook.mixin"]

    def stock_quantity_changed(self):
        """
        Trigger the Stock Quantity Change related Webhook Event
        """
        super().stock_quantity_changed()
        webhook_event = self.env.ref(
            "ol_webhooks.product_template_stock_quantity_changed"
        )
        webhook_event.trigger(records=self, operation_override="update")

    def system_stock_quantity_changed(self):
        """
        Trigger the System Stock Quantity Change related Webhook Event
        """
        super().system_stock_quantity_changed()
        webhook_event = self.env.ref("ol_webhooks.system_stock_quantity_changed")
        webhook_event.trigger(records=self, operation_override="update")

    def expected_date_changed(self):
        """
        Trigger the Expected Date Change related Webhook Event
        """

        webhook_event = self.env.ref(
            "ol_webhooks.product_template_stock_quantity_changed"
        )
        return webhook_event.trigger(records=self, operation_override="update")

    def system_expected_date_changed(self):
        """
        Trigger the Expected Date Change related Webhook Event
        """

        webhook_event = self.env.ref("ol_webhooks.system_stock_quantity_changed")
        return webhook_event.trigger(records=self, operation_override="update")

    def trigger_custom_events(self, products, values, _):
        """
        Call different `webhook.events` based on what is in the passed values
        """
        remaining_values = products.trigger_purchase_cost_webhook_event(values)
        return products, remaining_values

    def trigger_purchase_cost_webhook_event(self, values):
        """
        Trigger Pricing related fields
        """

        fields = ["purchase_cost", "purchase_cost_po_id", "purchase_cost_updated_at"]
        xml_id = "product_template_cost_changed"
        force_trigger = self.env.context.get(
            "force_trigger_purchase_cost_webhook_event", False
        )
        return self.trigger_custom_webhook_event(values, fields, xml_id, force_trigger)

    def trigger_custom_webhook_event(self, values, fields, xml_id, force_trigger=False):
        """
        Trigger a different events for different fields present in the fields
        Only pass on non Company records
        """

        trigger = False
        remaining_values = {}
        for field_name, field_value in values.items():
            if field_name in fields:
                trigger = True
            else:
                remaining_values[field_name] = field_value

        # If the create/write values contain `purchase_cost` information
        if (trigger or force_trigger) and self:
            # Find the specific `webhook.even` XML record
            webhook_event = self.env.ref(f"ol_webhooks.{xml_id}")
            webhook_event.trigger(records=self, operation_override="update")

        # Return the values we did not account for in this function
        return remaining_values
