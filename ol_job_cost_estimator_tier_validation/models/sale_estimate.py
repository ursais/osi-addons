# Import Odoo libs
from odoo import models


class SaleEstimateJob(models.Model):
    _name = "sale.estimate.job"
    _inherit = ["sale.estimate.job", "tier.validation"]
    _state_from = ["draft", "reject", "quotesend"]
    _state_to = ["confirm", "approve", "sent"]
    _cancel_state = ["cancel"]
    _tier_validation_manual_config = False
