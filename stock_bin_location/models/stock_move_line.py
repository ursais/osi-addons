# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    bin_location = fields.Char(string="Bin Location")

    def _action_done(self):
        result = super()._action_done()
        for record in self:
            if record.bin_location and record.lot_id:
                record.lot_id.bin_location = record.bin_location
        return result
