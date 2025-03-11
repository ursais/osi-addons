# Import Odoo libs
from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # COLUMNS ###

    component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Component History",
        related="lot_id.component_history_ids",
    )

    # END #######
    # METHODS #######

    def action_repair_done(self):
        res = super().action_repair_done()
        for repair in self:
            if repair.lot_id:
                for line in repair.move_ids:
                    if line.repair_line_type == "add":
                        type = "add"
                    elif line.repair_line_type == "remove":
                        type = "remove"
                    elif line.repair_line_type == "recycle":
                        type = "recycle"
                    self.env["component.history"].create(
                        {
                            "lot_id": repair.lot_id.id,
                            "product_id": line.product_id.id,
                            "qty_changed": line.product_uom_qty,
                            "change_type": type,
                            "source_id": f"repair.order,{repair.id}",
                            "component_lot_ids": [[6, 0, line.lot_ids.ids]],
                        }
                    )
        return res

    # END #######
