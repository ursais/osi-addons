# Import Odoo libs
from odoo import models


class SaleEstimateJob(models.Model):
    """Add the opportunity field to the create purchase request method on estimates."""

    _inherit = "sale.estimate.job"

    # METHODS ##########

    def action_create_purchase_request(self):
        ctx = self._context.copy()
        ctx.update({"default_opportunity_id": self.opportunity_id.id})
        return super(
            SaleEstimateJob, self.with_context(ctx)
        ).action_create_purchase_request()

    # END ##########
