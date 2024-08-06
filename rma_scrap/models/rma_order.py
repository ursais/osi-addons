# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_scrap_count(self):
        for order in self:
            scraps = order.mapped("rma_line_ids.scrap_ids")
            order.scrap_count = len(scraps)

    scrap_count = fields.Integer(compute="_compute_scrap_count", string="# Scrap")

    def action_view_scrap_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_stock_scrap")
        result = action.sudo().read()[0]
        scraps = self.env["stock.scrap"].search([("origin", "=", self.name)])
        if len(scraps) > 1:
            result["domain"] = [("id", "in", scraps.ids)]
        elif len(scraps) == 1:
            res = self.env.ref("stock.stock_scrap_form_view", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = scraps.ids[0]
        return result
