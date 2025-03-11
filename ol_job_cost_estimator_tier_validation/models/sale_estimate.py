# Import Odoo libs
from odoo import api, models


class SaleEstimateJob(models.Model):
    """
    Adding tier validation inheritance as well as state from/to definitions.
    We can now add a state into both from/to to trigger validations def checks.
    These definiation are used via the tier.validation abstract model.
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

    # METHODS #####

    @api.model
    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res.append("quotation_id")
        res.append("state")
        return res

    # END #########
