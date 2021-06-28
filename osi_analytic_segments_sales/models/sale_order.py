# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
