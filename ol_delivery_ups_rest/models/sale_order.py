# Import Python libs
import logging

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import models, fields, api

class SaleOrder(models.Model):
    """
    UPS Delivery related additions to the Sale Order Model
    """

    _inherit = "sale.order"

    ### COLUMNS #######
    is_ups_delivery = fields.Boolean(
        string="Is UPS Delivery", compute="_compute_is_ups_delivery", default=False, store=True
    )
    ups_request_log = fields.Text("UPS API Request Log", readonly=True, copy=False)
    ups_response_log = fields.Text("UPS API Response Log", readonly=True, copy=False)
    ### END COLUMNS ###

    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_ups_delivery(self):
        for order in self:
            order.is_ups_delivery = order.carrier_id and order.carrier_id.delivery_type in ["ups_rest", "ups"]
