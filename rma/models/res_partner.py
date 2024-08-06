# Copyright 2017-22 ForgeFlow
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_rma_line_count(self):
        for rec in self:
            rec.rma_line_count = len(rec.rma_line_ids)

    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line", string="RMAs", inverse_name="partner_id"
    )
    rma_line_count = fields.Integer(
        compute="_compute_rma_line_count", compute_sudo=True
    )

    def action_open_partner_rma(self):
        action = self.env.ref("rma.action_rma_customer_lines")
        result = action.sudo().read()[0]
        result["context"] = {"search_default_partner_id": self.id}
        result["domain"] = []
        result["display_name"] = "Partner RMAs"
        return result
