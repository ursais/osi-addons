# Import Python libs

# Import Odoo libs
from odoo import models


class SaleBooking(models.Model):
    """
    Add webhook compatibility to Bookings
    """

    _name = "sale.booking"
    _inherit = ["sale.booking", "webhook.mixin"]

    @staticmethod
    def get_webhook_trigger_computed_models():
        """
        We want to potentionaly trigger webhooks if related values for any of these object are written
        """
        return ["sale.order"]
