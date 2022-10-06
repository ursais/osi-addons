# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    bin_location = fields.Char(related="lot_id.bin_location", string="Bin Location")

    def _action_done(self):
        result = super()._action_done()
        for record in self.filtered(lambda m: m.exists() and m.bin_location and m.lot_id):
            record.lot_id.bin_location = record.bin_location
        return result
