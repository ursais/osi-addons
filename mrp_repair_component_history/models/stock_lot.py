# Import Odoo libs
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    # COLUMNS ###

    component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Component History",
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

    # METHODS #######

    def toggle_show_invisible(self):
        """Toggles the visibility of invisible component history records."""
        self.show_invisible = not self.show_invisible

    @api.depends("show_invisible", "component_history_ids")
    def _compute_visible_component_history_ids(self):
        for lot in self:
            if lot.show_invisible:
                lot.visible_component_history_ids = lot.component_history_ids
            else:
                lot.visible_component_history_ids = lot.component_history_ids.filtered(
                    lambda r: not r.invisible
                )

    def generate_component_history(self):
        ComponentHistory = self.env["component.history"]
        MrpProduction = self.env["mrp.production"]
        history_data = []

        for lot in self:
            if lot.component_history_ids:
                continue

            # ==== 1. Manufacturing Order History ====
            mo = MrpProduction.search([("lot_producing_id", "=", lot.id)], limit=1)
            if mo:
                for move in mo.move_raw_ids:
                    # If the move isn't done then we don't include in history
                    if move.state != "done":
                        continue

                    # Migrated MO stock moves aren't consistant so for historical MO's,
                    # we rely on the related bom line qty which should be more accurate
                    move_qty = 0.0
                    if move.bom_line_id:
                        move_qty = move.bom_line_id.product_qty

                    history_data.append(
                        {
                            "lot_id": lot.id,
                            "product_id": move.product_id.id,
                            "qty_changed": move_qty,
                            "change_type": "manufactured",
                            "source_id": "mrp.production,%d" % mo.id,
                            "component_lot_ids": [(6, 0, [l.id for l in move.lot_ids])],
                            "date": mo.date_finished,
                        }
                    )

            # ==== 2. Repair Order History ====
            repair_orders = self.env["repair.order"].search(
                [
                    ("lot_id", "=", lot.id),
                    ("state", "=", "done"),
                ]
            )
            for repair in repair_orders:
                for line in repair.move_ids:
                    if line.repair_line_type not in ("add", "remove", "recycle"):
                        continue
                    history_data.append(
                        {
                            "lot_id": repair.lot_id.id,
                            "product_id": line.product_id.id,
                            "qty_changed": line.product_uom_qty,
                            "change_type": line.repair_line_type,
                            "source_id": "repair.order,%d" % repair.id,
                            "component_lot_ids": [(6, 0, [l.id for l in line.lot_ids])],
                            "date": line.date,
                        }
                    )

        # Bulk create
        ComponentHistory.create(history_data)

    # END #######
