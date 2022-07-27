# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        for rec in self:
            if (
                (rec.lot_id or rec.lot_name)
                and rec.location_id.usage == "supplier"
                and rec.product_id.tracking == "serial"
            ):
                # Search for the quants in internal location having qty > 0
                # with same lot ID.
                quants = self.env["stock.quant"].search(
                    [
                        ("product_id", "=", rec.product_id.id),
                        ("location_id.usage", "not in", ["supplier", "customer"]),
                        ("quantity", ">", 0),
                        "|",
                        ("lot_id", "=", rec.lot_id.id),
                        ("lot_id.name", "=", rec.lot_name),
                    ],
                    order="id",
                )
                if quants:
                    quant_location = quants[0].location_id.display_name
                    raise ValidationError(
                        _(
                            "The serial number has already been assigned: \n "
                            "Product: %s, Serial Number: %s, Location: %s"
                        )
                        % (
                            rec.product_id.display_name,
                            rec.lot_id and rec.lot_id.name or rec.lot_name,
                            quant_location,
                        )
                    )
        res = super(StockMoveLine, self)._action_done()
        return res
