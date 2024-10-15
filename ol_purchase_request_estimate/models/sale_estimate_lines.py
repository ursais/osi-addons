# Import Odoo libs
from odoo import api, fields, models


class SaleEstimatelineJob(models.Model):
    """Add the ability to create PR from estimates and link their lines."""

    _inherit = "sale.estimate.line.job"

    # COLUMNS ######

    specifications = fields.Text()
    purchase_request_line_ids = fields.One2many(
        "purchase.request.line",
        "estimate_line_id",
        string="PR Lines",
    )
    purchase_cost = fields.Float(
        string="PO Cost", compute="_compute_purchase_cost", store=True
    )
    purchase_state = fields.Selection(
        selection=lambda self: self.env["purchase.order"]._fields["state"].selection,
        compute="_compute_purchase_state",
        store=True,
    )

    # END ##########
    # METHODS ##########

    @api.depends(
        "purchase_request_line_ids.purchase_state",
        "purchase_request_line_ids.purchase_lines.order_id.state",
        "purchase_request_line_ids.purchase_lines.price_unit",
    )
    def _compute_purchase_cost(self):
        for line in self:
            purchase_lines = line.mapped("purchase_request_line_ids.purchase_lines")
            line.purchase_cost = (
                sum(purchase_lines.mapped("price_unit")) / len(purchase_lines)
                if purchase_lines
                else 0.0
            )

    @api.depends(
        "purchase_request_line_ids.purchase_state",
        "purchase_request_line_ids.purchase_lines.state",
        "purchase_request_line_ids.purchase_lines.order_id.state",
    )
    def _compute_purchase_state(self):
        for line in self:
            states = line.mapped("purchase_request_line_ids.purchase_lines.state")
            if "done" in states:
                line.purchase_state = "done"
            elif states and all(state == "cancel" for state in states):
                line.purchase_state = "cancel"
            elif any(state in ("purchase", "to approve", "sent") for state in states):
                line.purchase_state = next(
                    (
                        state
                        for state in states
                        if state in ("purchase", "to approve", "sent")
                    ),
                    "draft",
                )
            else:
                line.purchase_state = "draft"

    # END ##########
