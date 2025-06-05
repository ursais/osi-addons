# Import Odoo libs
from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # METHODS #######

    def button_mark_done(self):
        res = super().button_mark_done()
        for production in self:
            if production.product_id.tracking == "serial":
                for lot in production.move_finished_ids.mapped("move_line_ids.lot_id"):
                    for move in production.move_raw_ids.filtered(
                        lambda m: m.state == "done"
                    ):
                        self.env["component.history"].create(
                            {
                                "lot_id": lot.id,
                                "product_id": move.product_id.id,
                                "qty_changed": move.quantity,
                                "change_type": "manufactured",
                                "source_id": f"mrp.production,{production.id}",
                                "component_lot_ids": [[6, 0, move.lot_ids.ids]],
                                "date": production.date_finished,
                            }
                        )
        return res

    # END #######
