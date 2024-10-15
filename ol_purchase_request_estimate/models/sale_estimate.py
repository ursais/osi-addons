# Import Odoo libs
from odoo import api, fields, models


class SaleEstimateJob(models.Model):
    """Add the ability to create PR's from Estimates."""

    _inherit = "sale.estimate.job"

    # COLUMNS ######

    purchase_request_ids = fields.One2many(
        "purchase.request",
        "estimate_id",
        string="Purchase Requests",
    )
    purchase_request_count = fields.Integer(
        string="Purchase requests",
        compute="_compute_purchase_request_count",
    )

    # END ##########
    # METHODS ##########

    def action_create_purchase_request(self):
        purchase_request = self.env["purchase.request"]
        purchase_request_line = self.env["purchase.request.line"]

        for estimate in self:

            # Create the Purchase Request
            purchase_request = purchase_request.create(
                {
                    "origin": estimate.number,
                    "requested_by": self.env.user.id,
                    "company_id": estimate.company_id.id,
                    "description": estimate.description or estimate.number,
                    "currency_id": estimate.currency_id.id,
                }
            )

            # Create the Purchase Request Lines
            for line in estimate.estimate_ids:
                purchase_request_line_vals = {
                    "request_id": purchase_request.id,
                    "product_id": line.product_id.id,
                    "name": line.product_description or line.product_id.display_name,
                    "product_qty": line.product_uom_qty,
                    "product_uom_id": line.product_uom.id,
                    "specifications": line.specifications,
                    "estimated_cost": line.price_unit,
                    "estimate_line_id": line.id,
                }
                purchase_request_line.create(purchase_request_line_vals)

            # Show the created purchase request
            return {
                "type": "ir.actions.act_window",
                "res_model": "purchase.request",
                "view_mode": "form",
                "res_id": purchase_request.id,
                "target": "current",
            }

    @api.depends("purchase_request_ids")
    def _compute_purchase_request_count(self):
        for request in self:
            request.purchase_request_count = len(request.purchase_request_ids)

    def action_view_purchase_request(self):
        purchase_requests = self.purchase_request_ids
        action = self.env.ref("purchase_request.purchase_request_form_action").read()[0]
        if len(purchase_requests) == 1:
            action["views"] = [
                (self.env.ref("purchase_request.view_purchase_request_form").id, "form")
            ]
            action["res_id"] = purchase_requests.id
        else:
            action["domain"] = [("id", "in", purchase_requests.ids)]
        return action

    # END ##########
