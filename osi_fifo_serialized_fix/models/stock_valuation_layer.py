# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many("stock.production.lot",
                               string="Lot ID's", readonly=True)
