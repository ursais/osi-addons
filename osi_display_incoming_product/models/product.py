# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Product(models.Model):
    _inherit = "product.product"

    def action_view_stock_move(self):
        for variant in self:
            final_move_ids = []
            move_ids = self.env["stock.move"].search(
                [
                    ("product_id", "=", variant.id),
                    (
                        "state",
                        "in",
                        ["waiting", "confirmed", "assigned", "partially_available"],
                    ),
                    ("location_id.usage", "not in", ("internal", "transit")),
                    ("location_dest_id.usage", "in", ("internal", "transit")),
                ]
            )
            final_move_ids += move_ids.ids
        action = self.env.ref(
            "osi_display_incoming_product.action_receipt_picking_move"
        ).read()[0]
        action["domain"] = [("id", "in", final_move_ids)]
        return action
