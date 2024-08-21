# Import Odoo libs
from odoo import models


class SaleEstimateJob(models.Model):
    """
    Adding tier validation inheritance as well as state from/to definitions.
    We can now add a state into both from/to to trigger validations def checks.
    """

    _name = "sale.estimate.job"
    _inherit = ["sale.estimate.job", "tier.validation"]
    _state_from = [
        "draft",
        "reject",
        "sent",
        "quotesend",
        "confirm",
    ]
    _state_to = [
        "confirm",
        "sent",
        "quotesend",
        "approve",
    ]
    _cancel_state = ["cancel"]
    _tier_validation_manual_config = False
