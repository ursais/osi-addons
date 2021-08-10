# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class PurchaseSubscription(models.Model):
    _inherit = "purchase.subscription"

    def _get_default_segment_one(self):
        return self.env["analytic.segment.one"].get_default_segment_one()

    analytic_segment_one_id = fields.Many2one(
        "analytic.segment.one",
        string="Analytic Segment One",
        default=_get_default_segment_one,
        copy=False,
    )
    analytic_segment_two_id = fields.Many2one(
        "analytic.segment.two", string="Analytic Segment Two", copy=False
    )

    def _prepare_invoice_line(self, line, fiscal_position):
        res = super()._prepare_invoice_line(line, fiscal_position)
        res.update(
            {
                "analytic_segment_one_id": line.analytic_segment_one_id.id,
                "analytic_segment_two_id": line.analytic_segment_two_id.id,
            }
        )
        return res
