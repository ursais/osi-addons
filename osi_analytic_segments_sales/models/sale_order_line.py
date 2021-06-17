# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_default_segment_one(self):
        return self.env["analytic.segment.one"].get_default_segment_one()

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        help="The analytic account related to a sales order Line.",
        copy=False,
    )
    analytic_segment_one_id = fields.Many2one(
        "analytic.segment.one",
        string="Analytic Segment One",
        default=_get_default_segment_one,
        copy=False,
    )
    analytic_segment_two_id = fields.Many2one(
        "analytic.segment.two", string="Analytic Segment Two", copy=False
    )

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super()._prepare_invoice_line(qty)
        res.update(
            {
                "analytic_segment_one_id": self.order_id.analytic_segment_one_id.id,
                "analytic_segment_two_id": self.order_id.analytic_segment_two_id.id,
            }
        )
        return res
