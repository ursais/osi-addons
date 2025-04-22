# Import Odoo libs
from odoo import models


class DeliveryCarrier(models.Model):
    """
    Add UUID compatibility
    """

    _name = "delivery.carrier"
    _inherit = ["delivery.carrier", "res.uuid"]
