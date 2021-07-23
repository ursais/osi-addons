# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    rma_count = fields.Integer("# RMA Orders", compute="_compute_rma_count")

    def _compute_rma_count(self):
        for ag_rec in self:
            ag_rec.rma_count = self.env["rma.order.line"].search_count(
                [("agreement_id", "in", ag_rec.ids)]
            )
