# Copyright (C) 2023, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _create_out_svl(self, forced_quantity=None):
        res = self.env["stock.valuation.layer"]
        for move in self:
            result = super(
                StockMove, move.with_context(stock_move_id=move)
            )._create_out_svl(forced_quantity)
            res += result
        return res
