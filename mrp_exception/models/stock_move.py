# Copyright (C) 2024, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = ["stock.move", "base.exception.method"]
    _name = "stock.move"

    ignore_exception = fields.Boolean(
        related="raw_material_production_id.ignore_exception",
        store=True,
        string="Ignore Exceptions",
    )

    def _get_main_records(self):
        return self.mapped("raw_material_production_id")

    @api.model
    def _reverse_field(self):
        return "production_ids"

    def _detect_exceptions(self, rule):
        records = super()._detect_exceptions(rule)
        return records.mapped("raw_material_production_id")
