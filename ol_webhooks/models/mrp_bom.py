# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api


class MrpBom(models.Model):
    """
    Trigger stock picking messages when tracking number records are changed
    """

    _inherit = "mrp.bom"

    def write(self, vals):
        """
        Trigger RO webhook when the TA bom is edited
        """
        res = super().write(vals)

        repair_orders = self.mapped("ta_repair_order_id")

        if repair_orders:
            webhook_event = self.env.ref(f"ol_webhooks.support_repair_order_update")

            if repair_orders and webhook_event:
                # If the filter returned any records and we found the `webhook.event`
                webhook_event.trigger(
                    records=repair_orders, operation_override="update"
                )

        return res
