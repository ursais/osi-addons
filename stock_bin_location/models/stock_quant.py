# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    bin_location = fields.Char(compute="_compute_bin_location", string="Bin Location", store=True)

    @api.depends("lot_id", "lot_id.bin_location")
    def _compute_bin_location(self):
        for record in self:
            if record.lot_id and record.lot_id.bin_location:
                record.bin_location = record.lot_id.bin_location or False
