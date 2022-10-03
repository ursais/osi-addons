# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    bin_location = fields.Char(string="Bin Location")
