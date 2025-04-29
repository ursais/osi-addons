# Import Python Libs

# Import Odoo Libs
from odoo import models


class MrpProduction(models.Model):
    """
    Add webhook compatibility to mrp production records
    """

    _name = "mrp.production"
    _inherit = ["mrp.production", "webhook.mixin"]

    def action_cancel(self):
        """
        If an MO that is in progress gets cancelled, send a message
        """
        super().action_cancel()

        if self.state in ["progress", "to_close"]:
            webhook_event = self.env.ref("ol_webhooks.manufacturing_order_update")
            webhook_event.trigger(records=self, operation_override="update")

    def button_mark_done(self):
        """
        Send a message when the MO is completed
        """
        super().button_mark_done()

        webhook_event = self.env.ref("ol_webhooks.manufacturing_order_update")
        webhook_event.trigger(records=self, operation_override="update")

    # TODO: This functionality does not exist in odoo 17. Some version likely will in the future but the decision has not been made as of 4/22/25 (re: Jeff)
    # def button_add_or_update_serial_numbers(self):
    #     """
    #     Send messages if an in progress MO has it's serial numbers edited
    #     """
    #     super().button_add_or_update_serial_numbers

    #     if self.state in ["progress", "to_close"]:
    #         webhook_event = self.env.ref("ol_webhooks.manufacturing_order_update")
    #         webhook_event.trigger(records=self, operation_override="update")
