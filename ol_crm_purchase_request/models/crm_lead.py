from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = "crm.lead"

    purchase_request_ids = fields.One2many("purchase.request", "opportunity_id")
    purchase_request_count = fields.Integer(
        string="Purchase Request", compute="_compute_purchase_request_count"
    )

    def _compute_purchase_request_count(self):
        for lead in self:
            lead.purchase_request_count = len(lead.purchase_request_ids)

    def action_view_purchase_request(self):
        purchase_request_ids = self.purchase_request_ids
        action = self.env.ref("purchase_request.purchase_request_form_action").read()[0]
        action["context"] = {"create": False}
        if len(purchase_request_ids) == 1:
            action["views"] = [
                (
                    self.env.ref("purchase_request.view_purchase_request_form").id,
                    "form",
                )
            ]
            action["res_id"] = purchase_request_ids.id
        else:
            action["domain"] = [("id", "in", purchase_request_ids.ids)]
        return action
