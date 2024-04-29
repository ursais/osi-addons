# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_substitute_product = fields.Selection(
        [("yes", "YES")], compute="_compute_substitute_info", string="Substitutes"
    )

    def _compute_substitute_info(self):
        for rec in self:
            rec.is_substitute_product = False
            if rec.bom_line_id and rec.bom_line_id.substitute_product_ids:
                rec.is_substitute_product = "yes"
