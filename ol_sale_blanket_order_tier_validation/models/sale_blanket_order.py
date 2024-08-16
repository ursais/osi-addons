# Import Odoo libs
from odoo import models


class SaleBlanketOrder(models.Model):
    _name = "sale.blanket.order"
    _inherit = ["sale.blanket.order", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["open", "done", "expired"]
    _cancel_state = ["cancel"]
    _tier_validation_manual_config = False
