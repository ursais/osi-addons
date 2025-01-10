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
    url = fields.Char(string="URL")
    product_type = fields.Selection(related="product_id.detailed_type")
    forecasted_issue = fields.Boolean(compute="_compute_forecasted_issue")

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

    @api.depends("product_qty", "date_required")
    def _compute_forecasted_issue(self):
        for line in self:
            warehouse = line.request_id.picking_type_id.warehouse_id
            line.forecasted_issue = False
            if line.product_id:
                virtual_available = line.product_id.with_context(
                    warehouse=warehouse.id, to_date=line.date_required
                ).virtual_available
                if virtual_available <= 0:
                    line.forecasted_issue = True

    def action_product_forecast_report(self):
        self.ensure_one()
        action = self.product_id.action_product_forecast_report()
        action["context"] = {
            "active_id": self.product_id.id,
            "active_model": "product.product",
            "move_to_match_ids": self.purchase_lines.move_ids.filtered(
                lambda m: m.product_id == self.product_id
            ).ids,
            "purchase_line_to_match_id": self.purchase_lines.id,
        }
        warehouse = self.request_id.picking_type_id.warehouse_id
        if warehouse:
            action["context"]["warehouse"] = warehouse.id
        return action

    # END ##########
