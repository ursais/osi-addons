# Import Odoo libs
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """Add Smart Button For Linked Up to Purchase Request"""

    _inherit = "purchase.order"

    # COLUMNS ######
    purchase_request_line_count = fields.Integer("Purchase Request line Count",compute="_compute_purchase_request_line_count")
    # END ##########
    
    # METHODS ######
    def action_open_purchase_request_line(self):
        action = (
            self.env.ref("purchase_request.purchase_request_line_form_action")
            .sudo()
            .read()[0]
        )
        lines = self.order_line.purchase_request_lines
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("purchase_request.purchase_request_line_form").id, "form")
            ]
            action["res_id"] = lines.ids[0]
        return action

    def _compute_purchase_request_line_count(self):
        for po in self:
            po.purchase_request_line_count = len(po.order_line.purchase_request_lines)
    # END ##########

