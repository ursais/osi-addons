# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    bin_location = fields.Char(
        related="lot_id.bin_location",
        string="Bin Location",
        store=True,
    )
    get_bin_location = fields.Char(string="Get Bin Location")

    def _action_done(self):
        res = super()._action_done()
        if self._context.get("button_validate_picking_ids"):
            stock_picking_id = self.env["stock.picking"].browse(
                self._context.get("button_validate_picking_ids")
            )

            for ml in stock_picking_id.move_line_ids.filtered(
                lambda l: l.product_id.tracking != "none"
            ):
                if ml.get_bin_location and (
                    ml.lot_id.bin_location != ml.get_bin_location
                    or not ml.lot_id.bin_location
                ):
                    ml.lot_id.write({"bin_location": ml.get_bin_location})
        return res
