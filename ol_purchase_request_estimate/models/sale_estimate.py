# Import Odoo libs
from odoo import api, fields, models


class SaleEstimateJob(models.Model):
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
        # Create Purchase Request from Sale request
        purchase_request_vals = {
            "requested_by": self.env.user.id,
            "origin": self.number,
            # "request_line": [
            #     (
            #         0,
            #         0,
            #         {
            #             "product_id": line.product_id.id,
            #             "product_qty": line.product_uom_qty,
            #             "product_uom": line.product_uom.id,
            #             "price_unit": line.price_unit,
            #             "name": line.name,
            #         },
            #     )
            #     for line in self.request_line
            # ],
        }
        purchase_request = self.env["purchase.request"].create(purchase_request_vals)
        action = self.env.ref("purchase_request.purchase_request_form_action").read()[0]
        action["views"] = [
            (self.env.ref("purchase_request.view_purchase_request_form").id, "form")
        ]
        action["res_id"] = purchase_request.id
        return action

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
