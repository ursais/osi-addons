# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_matching_bom(self, product_id, company_id, values):
        moves = values.get("move_dest_ids")
        bom_id = moves[0].sale_line_id.bom_id if moves else None
        if bom_id:
            values.update(bom_id=bom_id)
        return super(StockRule, self)._get_matching_bom(
            product_id=product_id, company_id=company_id, values=values
        )
