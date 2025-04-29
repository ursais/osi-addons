# Import Python Libs

# Import Odoo Libs
from odoo import models, api


class TrackingNumber(models.Model):
    """
    Trigger stock picking messages when tracking number records are changed
    """

    _inherit = "tracking.number"

    @api.model
    def create(self, vals):
        """
        Trigger a Webhook Request for the related stock picking record when a tracking number is created
        """
        res = super(TrackingNumber, self).create(vals)
        res.picking_id.trigger_delivery_order_webhook()

        return res

    def write(self, vals):
        """
        Trigger a Webhook Request for the related stock picking record when a tracking number is edited
        """
        res = super(TrackingNumber, self).write(vals)
        self.picking_id.trigger_delivery_order_webhook()

        return res

    def unlink(self):
        """
        Trigger a Webhook Request for the related stock picking record when a tracking number is deleted
        """
        stock_picking = self.picking_id
        res = super(TrackingNumber, self).unlink()
        stock_picking.trigger_delivery_order_webhook()

        return res
