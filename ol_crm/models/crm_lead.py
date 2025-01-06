# Import Odoo libs
from odoo import api, fields, models


class CRMLead(models.Model):
    """Add the ability to create Estimate's from Leads."""

    _inherit = "crm.lead"

    # COLUMNS ######

    estimate_ids = fields.One2many(
        "sale.estimate.job",
        "opportunity_id",
        string="Estimates",
    )
    estimate_count = fields.Integer(
        string="Estimate Count",
        compute="_compute_estimate_count",
    )
    quantity = fields.Integer()

    # END ##########
    # METHODS ##########

    def action_create_estimate(self):
        """Action called via button to create a new estimate."""
        # Create the estimate
        new_estimate = self.env["sale.estimate.job"].create(
            {
                "partner_id": self.partner_id.id,
                "pricelist_id": self.partner_id.property_product_pricelist.id,
                "company_id": self.company_id.id,
                "user_id": self.user_id.id or self.env.user.id,
                "team_id": self.team_id.id,
                "payment_term_id": self.partner_id.property_payment_term_id.id,
                "opportunity_id": self.id,
            }
        )

        # Show the created estimate
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.estimate.job",
            "view_mode": "form",
            "res_id": new_estimate.id,
            "target": "current",
        }

    @api.depends("estimate_ids")
    def _compute_estimate_count(self):
        """Standard count method to count related Estimate's for smart button."""
        for lead in self:
            lead.estimate_count = len(lead.estimate_ids)

    def action_view_estimate(self):
        """Smart button action to open the Estimate or list of Estimate's if more than one."""
        estimates = self.estimate_ids
        action = self.env.ref("job_cost_estimate_customer.action_estimate_job").read()[
            0
        ]
        if len(estimates) == 1:
            action["views"] = [
                (
                    self.env.ref(
                        "job_cost_estimate_customer.view_sale_estimate_form_job"
                    ).id,
                    "form",
                )
            ]
            action["res_id"] = estimates.id
        else:
            action["domain"] = [("id", "in", estimates.ids)]
        return action

    # END ##########
