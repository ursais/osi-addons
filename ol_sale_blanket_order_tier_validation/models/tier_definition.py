# Import Odoo libs
from odoo import api, models


class TierDefinition(models.Model):
    """
    Add Sale Blanket Order model to tier definitions.
    """

    _inherit = "tier.definition"

    # METHODS #########

    @api.model
    def _get_tier_validation_model_names(self):
        """This method adds the Sale Blanket Order model to tier definitions."""
        res = super()._get_tier_validation_model_names()
        res.append("sale.blanket.order")
        return res

    # END ######
