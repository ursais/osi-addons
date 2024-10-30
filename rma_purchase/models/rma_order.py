# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_po_count(self):
        for rec in self:
            po_count = 0
            rma_line_po = []
            for line in rec.rma_line_ids:
                rma_line_po += (
                    self.env["purchase.order"].search([("origin", "=", line.name)]).ids
                )
            if rma_line_po:
                po_count = len(list(set(rma_line_po)))
            rec.po_count = po_count

    @api.depends("rma_line_ids")
    def _compute_origin_po_count(self):
        for rma in self:
            purchases = rma.mapped("rma_line_ids.purchase_order_line_id.order_id")
            rma.origin_po_count = len(purchases)

    po_count = fields.Integer(compute="_compute_po_count", string="# of PO")
    origin_po_count = fields.Integer(
        compute="_compute_origin_po_count", string="# of Origin PO"
    )

    def action_view_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq")
        result = action.sudo().read()[0]
        po_ids = self.env["purchase.order"].search([("origin", "=", self.name)]).ids
        for line in self.rma_line_ids:
            po_ids += (
                self.env["purchase.order"].search([("origin", "=", line.name)]).ids
            )
        result["domain"] = [("id", "in", po_ids)]
        return result

    def action_view_origin_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq")
        result = action.sudo().read()[0]
        po_ids = self.mapped("rma_line_ids.purchase_order_line_id.order_id").ids
        result["domain"] = [("id", "in", po_ids)]
        return result
