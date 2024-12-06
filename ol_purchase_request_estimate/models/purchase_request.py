# Import Odoo libs
from odoo import api, fields, models


class PurchaseRequest(models.Model):
    """Add relation to estimates on PR's"""

    _inherit = "purchase.request"

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(
            self.env.context.get("company_id") or self.env.company.id
        )

    # COLUMNS ######

    estimate_id = fields.Many2one(
        "sale.estimate.job",
        string="Sale Estimate",
    )
    estimate_count = fields.Integer(
        compute="_compute_estimate_count",
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Deliver To",
        required=True,
        default=_default_picking_type,
        help="This will determine operation type of incoming shipment",
    )

    # END ##########
    # METHODS ##########

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not picking_type:
            picking_type = self.env["stock.picking.type"].search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return picking_type[:1]

    @api.onchange("company_id")
    def _onchange_company_id(self):
        p_type = self.picking_type_id
        if not (
            p_type
            and p_type.code == "incoming"
            and (
                p_type.warehouse_id.company_id == self.company_id
                or not p_type.warehouse_id
            )
        ):
            self.picking_type_id = self._get_picking_type(self.company_id.id)

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
