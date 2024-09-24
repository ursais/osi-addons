# Import Odoo libs
from odoo import api, fields, models


class SaleEstimateLineJob(models.Model):
    """
    Add customer_lead field Sale Estimate Line
    """

    _inherit = "sale.estimate.line.job"

    # COLUMNS #####

    customer_lead = fields.Float(
        compute="_compute_customer_lead",
        store=True,
        readonly=False,
        precompute=True
    )

    # END #########

    # METHODS #####

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay or 0.0

    # END #########
