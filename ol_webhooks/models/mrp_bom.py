# Import Python Libs

# Import Odoo Libs
from odoo import models


class MrpBom(models.Model):
    """
    Trigger stock picking messages when tracking number records are changed
    """

    _name = "mrp.bom"
    _inherit = ["mrp.bom", "webhook.mixin"]

    def write(self, vals):
        """
        Trigger RO webhook when the TA bom is edited
        """
        res = super().write(vals)
        # TODO: (4/23/2025) The tech support/RMA process has not been accepted by the users yet, so this functionality is still up in the air.
        # repair_orders = self.mapped("ta_repair_order_id")

        # if repair_orders:
        #     webhook_event = self.env.ref(f"ol_webhooks.support_repair_order_update")

        #     if repair_orders and webhook_event:
        #         # If the filter returned any records and we found the `webhook.event`
        #         webhook_event.trigger(
        #             records=repair_orders, operation_override="update"
        #         )

        return res
