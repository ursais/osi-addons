# Import Odoo libs
from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # COLUMNS ###

    component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Component History",
        related="lot_id.component_history_ids",
    )
    show_invisible = fields.Boolean(
        string="Show All History",
        default=True,
        help="By default, only 'current' components are shown so if a component was removed the removed line will show and the original is hidden. Click to see the full history.",
    )
    visible_component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Visible Component History",
        compute="_compute_visible_component_history_ids",
    )

    # END #######
    # METHODS #######

    def toggle_show_invisible(self):
        """Toggles the visibility of invisible component history records."""
        self.show_invisible = not self.show_invisible

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
                            "date": line.date,
                        }
                    )
        return res

    @api.depends(
        "show_invisible",
        "component_history_ids",
    )
    def _compute_visible_component_history_ids(self):
        for lot in self:
            if lot.show_invisible:
                lot.visible_component_history_ids = lot.component_history_ids
            else:
                lot.visible_component_history_ids = lot.component_history_ids.filtered(
                    lambda r: not r.invisible
                )

    def generate_component_history(self):
        for repair in self:
            if repair.lot_id and not repair.lot_id.component_history_ids:
                repair.lot_id.generate_component_history()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            lot_id = vals.get("lot_id")
            if lot_id:
                lot = self.env["stock.lot"].browse(lot_id)
                if not lot.component_history_ids:
                    lot.generate_component_history()
        return super().create(vals)

    # END #######
