# Import Odoo libs
from odoo import api, fields, models


class PurchaseRequestLine(models.Model):
    """Add cost and estimate fields to PR Lines"""

    _inherit = "purchase.request.line"

    # COLUMNS ######

    purchase_cost = fields.Float(
        string="PO Cost",
        compute="_compute_purchase_cost",
        store=True,
    )
    estimate_line_id = fields.Many2one(
        "sale.estimate.line.job",
        string="Sale Estimate Line",
    )

    # END ##########
    # METHODS ##########

    @api.depends(
        "purchase_lines.order_id.state",
        "purchase_lines.price_unit",
    )
    def _compute_purchase_cost(self):
        """Method to compute add the purchasing cost to the PR line."""
        for line in self:
            purchase_lines = line.purchase_lines
            line.purchase_cost = (
                sum(purchase_lines.mapped("price_unit")) / len(purchase_lines)
                if purchase_lines
                else 0.0
            )

    # END ##########
