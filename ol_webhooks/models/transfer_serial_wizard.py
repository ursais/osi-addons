# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api


class TransferSerialNumberWizard(models.TransientModel):
    """
    Trigger MO webhook messages when serial numbers are transferred, for both origin and destination MO
    """

    _inherit = "mrp.production.serial.transfer.wizard"

    def action_transfer(self):
        res = super().action_transfer()

        webhook_event = self.env.ref("ls_webhooks.manufacturing_order_update")
        webhook_event.trigger(
            records=self.source_production_id, operation_override="update"
        )

        webhook_event = self.env.ref("ls_webhooks.manufacturing_order_update")
        webhook_event.trigger(
            records=self.current_production_id, operation_override="update"
        )
