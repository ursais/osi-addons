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
        string="PO Unit Cost",
        compute="_compute_purchase_cost",
        store=True,
    )
    purchase_state = fields.Char(
        string="Purchase Status",
        compute="_compute_purchase_state",
    )

    # END ##########
    # METHODS ##########

    @api.depends(
        "purchase_request_line_ids.purchase_state",
        "purchase_request_line_ids.purchase_lines.order_id.state",
        "purchase_request_line_ids.purchase_lines.price_unit",
    )
    def _compute_purchase_cost(self):
        """Method to compute add the purchasing cost to the estimate line."""
        for line in self:
            purchase_lines = line.mapped("purchase_request_line_ids.purchase_lines")
            line.purchase_cost = (
                sum(purchase_lines.mapped("price_unit")) / len(purchase_lines)
                if purchase_lines
                else 0.0
            )

    # Dictionary to map state codes to their labels
    STATE_LABELS = {
        "draft": "RFQ",
        "sent": "RFQ Sent",
        "to approve": "To Approve",
        "purchase": "Purchase Order",
        "done": "Done",
        "cancel": "Cancelled",
    }

    @api.depends("purchase_request_line_ids.purchase_state")
    def _compute_purchase_state(self):
        """This method will cycle through the related PR lines and set the
        purchase_state based on the PO state. This allows the user to see
        PO progress for each line directly on the estimate."""
        for line in self:
            states = line.purchase_request_line_ids.mapped("purchase_state")
            if states:
                # Filter out any `False` or invalid states
                state_labels = [
                    self.STATE_LABELS.get(state, state) for state in states if state
                ]
                line.purchase_state = (
                    ", ".join(state_labels) if state_labels else "No PO"
                )
            else:
                line.purchase_state = "No PR"

    # END ##########
