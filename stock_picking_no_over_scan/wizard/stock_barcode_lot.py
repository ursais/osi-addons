# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class StockBarcodeLot(models.TransientModel):
    _inherit = "stock_barcode.lot"

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        if self.qty_done > self.qty_reserved:
            raise ValidationError(
                _("The quantity done cannot be greater than the quantity "
                  "reserved."))


class StockBarcodeLotLine(models.TransientModel):
    _inherit = "stock_barcode.lot.line"

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        if self.qty_done > self.qty_reserved:
            raise ValidationError(
                _("The quantity done cannot be greater than the quantity "
                  "reserved."))
