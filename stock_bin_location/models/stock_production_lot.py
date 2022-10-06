# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    bin_location = fields.Char(string="Bin Location")

    def open_form_view(self):
        return {
            'res_model': 'stock.production.lot',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('stock.view_production_lot_form').id,
        }
