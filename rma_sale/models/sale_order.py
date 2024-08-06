# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line", compute="_compute_rma_line"
    )

    rma_count = fields.Integer(compute="_compute_rma_count", string="# of RMA")

    def _compute_rma_count(self):
        for so in self:
            rmas = self.mapped("rma_line_ids")
            so.rma_count = len(rmas)

    def _compute_rma_line(self):
        for so in self:
            so.rma_line_ids = so.mapped("order_line.rma_line_id")

    def action_view_rma(self):
        action = self.env.ref("rma.action_rma_customer_lines")
        result = action.sudo().read()[0]
        rma_ids = self.mapped("rma_line_ids").ids
        if rma_ids:
            # choose the view_mode accordingly
            if len(rma_ids) > 1:
                result["domain"] = [("id", "in", rma_ids)]
            else:
                res = self.env.ref("rma.view_rma_line_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = rma_ids[0]
        return result
