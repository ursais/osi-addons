# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_segment_one_id = fields.Many2one(related="move_id.analytic_segment_one_id")
    analytic_segment_two_id = fields.Many2one(related="move_id.analytic_segment_two_id")
