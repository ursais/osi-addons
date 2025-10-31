# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

            # If MO exists but not completed, warn the user
            if mo and mo.state not in ("draft", "done"):
                state_label = dict(mo._fields["state"].selection).get(
                    mo.state, mo.state
                )
                raise ValidationError(
                    _(
                        "The Manufacturing Order %s for serial '%s' is not completed "
                        "(State = %s).\n\nPlease complete it then the component "
                        "history will be populated."
                    )
                    % (mo.name, lot.name, state_label)
                )

            if mo:
                # Case 1a: Normal behavior - MO has valid raw moves
                if mo.move_raw_ids:
                    for move in mo.move_raw_ids:
                        if move.state != "done":
                            continue

                        move_qty = (
                            move.bom_line_id.product_qty if move.bom_line_id else 0.0
                        )

                        history_data.append(
                            {
                                "lot_id": lot.id,
                                "product_id": move.product_id.id,
                                "qty_changed": move_qty,
                                "change_type": "manufactured",
                                "source_id": f"mrp.production,{mo.id}",
                                "component_lot_ids": [
                                    (6, 0, [l.id for l in move.lot_ids])
                                ],
                                "date": mo.date_finished,
                            }
                        )

                # Case 1b: Fallback - MO has no component moves
                # Unless Odoo fixes their migration script, some older, migrated MO's
                # don't have components as they were consumed on the primary MO.
                # Look at the BoM in this scenario.
                else:
                    # Get BoM for this MO
                    bom = mo.bom_id
                    if bom:
                        for line in bom.bom_line_ids:
                            history_data.append(
                                {
                                    "lot_id": lot.id,
                                    "product_id": line.product_id.id,
                                    "qty_changed": line.product_qty,
                                    "change_type": "manufactured",
                                    "source_id": f"mrp.production,{mo.id}",
                                    "component_lot_ids": [
                                        (6, 0, [])
                                    ],  # No specific component lots known
                                    "date": mo.date_finished or mo.create_date,
                                }
                            )

            # ==== 2. Repair Order History ====
            repair_orders = self.env["repair.order"].search(
                [("lot_id", "=", lot.id), ("state", "=", "done")]
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
                            "source_id": f"repair.order,{repair.id}",
                            "component_lot_ids": [(6, 0, [l.id for l in line.lot_ids])],
                            "date": line.date,
                        }
                    )

        # ==== 3. Bulk Create History ====
        if history_data:
            ComponentHistory.create(history_data)

    # END #######
