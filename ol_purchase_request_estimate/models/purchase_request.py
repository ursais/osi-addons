# Import Odoo libs
from odoo import fields, models


class PurchaseRequest(models.Model):
    """Add relation to estimates on PR's"""

    _inherit = "purchase.request"

    # COLUMNS ######

    estimate_id = fields.Many2one(
        "sale.estimate.job",
        string="Sale Estimate",
    )
    estimate_count = fields.Integer(
        compute="_compute_estimate_count",
    )

    # END ##########
    # METHODS ##########

    def _compute_estimate_count(self):
        """Standard count method that shows on the smart button."""
        for request in self:
            request.estimate_count = self.env["sale.estimate.job"].search_count(
                [("id", "=", request.estimate_id.id)]
            )

    def action_view_estimate(self):
        """Smart button action to open the estimate or list of estimate's
        if more than one."""
        self.ensure_one()
        estimate_jobs = self.env["sale.estimate.job"].search(
            [("id", "=", self.estimate_id.id)]
        )
        action = self.env.ref("job_cost_estimate_customer.action_estimate_job").read()[
            0
        ]
        if len(estimate_jobs) == 1:
            action["views"] = [
                (
                    self.env.ref(
                        "job_cost_estimate_customer.view_sale_estimate_form_job"
                    ).id,
                    "form",
                )
            ]
            action["res_id"] = estimate_jobs.id
        else:
            action["domain"] = [("id", "in", estimate_jobs.ids)]
        return action

    # END ##########
