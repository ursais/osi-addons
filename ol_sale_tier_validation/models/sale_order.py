# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """
    Inherit sale order to change state from/to definitions for Tier Validation Usage
    """

    _name = "sale.order"
    _inherit = ["sale.order", "tier.validation"]

    _state_from = ["draft"]
    _state_to = ["sent", "sale"]
