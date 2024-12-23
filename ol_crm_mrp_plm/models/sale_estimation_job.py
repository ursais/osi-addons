from odoo import fields, models


class SaleEstimateJob(models.Model):
    _inherit = "sale.estimate.job"

    def action_create_eco_and_product(self, product_name, type):
        ctx = self._context.copy()
        ctx.update({"default_opportunity_id": self.opportunity_id.id})
        return super(
            SaleEstimateJob, self.with_context(ctx)
        ).action_create_eco_and_product(product_name, type)
