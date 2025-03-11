# Import Odoo libs
from odoo import models


class SaleEstimateJob(models.Model):
    """Add the new opportunity field to create ECO/Product method."""

    _inherit = "sale.estimate.job"

    # METHODS ##########

    def action_create_eco_and_product(self, product_name, type):
        ctx = self._context.copy()
        ctx.update({"default_opportunity_id": self.opportunity_id.id})

    # END ##########
