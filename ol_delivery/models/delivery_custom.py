from odoo import models, fields, _

import logging

_logger = logging.getLogger(__name__)


class ProviderCustom(models.Model):
    _inherit = "delivery.carrier"

    ### COLUMNS #######
    delivery_type = fields.Selection(
        selection_add=[("custom", "Custom"), ("none", "None")],
        ondelete={
            "custom": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            ),
            "none": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            ),
        },
    )

    ### END COLUMNS ###

    def none_rate_shipment(self, order):
        """
        Return the sale order's manual price
        """

        price = order.manual_delivery_price

        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def custom_rate_shipment(self, order):
        """
        Return the sale order's manual price
        """

        price = order.manual_delivery_price

        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }
