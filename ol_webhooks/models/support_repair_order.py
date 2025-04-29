# Import Python Libs
import logging

# Import Odoo Libs
from odoo import models, api


class RepairOrder(models.Model):
    """
    Trigger repair order messages
    """

    _name = "support.repair.order"
    _inherit = ["support.repair.order", "webhook.mixin"]
