# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairBatchEndConfirmWizard(models.TransientModel):
    """Wizard to let user modify consumption when ending repairs from batch."""

    _name = "repair.batch.end.confirm.wizard"
    _description = "Confirm Repair Quantity Differences"

    # COLUMNS ###

    batch_id = fields.Many2one(
        "repair.batch",
        string="Batch",
        required=True,
    )
    repair_ids = fields.Many2many(
        "repair.order",
        string="Repairs to Confirm",
    )
    move_ids = fields.Many2many(
        "stock.move",
        string="Moves with mismatched quantities",
        readonly=False,
        domain=[("repair_line_type", "=", "add")],
    )

    # END #######
    # METHODS ###

    @api.model
    def default_get(self, fields):
        """Preload all mismatched repair moves and their repairs with latest DB values."""
        res = super().default_get(fields)
        batch_id = self.env.context.get("default_batch_id")
        repair_ids_ctx = self.env.context.get("default_repair_ids", [])
        repair_ids = self.env["repair.order"].browse(repair_ids_ctx)

        if batch_id:
            batch = self.env["repair.batch"].browse(batch_id)
            # Add all repairs still under repair
            repair_ids |= batch.repair_ids.filtered(lambda r: r.state == "under_repair")

        # Fetch all relevant 'add' moves from DB (avoid cached values)
        moves = self.env["stock.move"].search(
            [
                ("repair_id", "in", repair_ids.ids),
                ("repair_line_type", "=", "add"),
                ("state", "!=", "done"),
                ("state", "!=", "cancel"),
            ]
        )
        # Filter only mismatched quantities
        mismatched_moves = moves.filtered(lambda m: m.product_uom_qty != m.quantity)

        res["repair_ids"] = [(6, 0, repair_ids.ids)]
        res["move_ids"] = [(6, 0, mismatched_moves.ids)]
        res["batch_id"] = batch_id
        return res

    def action_apply_and_end_repairs(self):
        """Apply quantity updates and end all repairs immediately."""
        if not self.move_ids:
            raise UserError("No mismatched repair moves found to update.")

        # Apply user-updated quantities move by move
        for move in self.move_ids:
            move.write(
                {
                    "product_uom_qty": move.product_uom_qty,
                    "quantity": move.quantity,
                }
            )

        # Recompute reservations for all relevant moves
        self.move_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
        )._action_assign()

        # End all repairs in this wizard
        self.repair_ids.filtered(
            lambda r: r.state == "under_repair"
        ).action_repair_end()

        # Update batch state
        if self.batch_id:
            self.batch_id._update_batch_state()

        return {"type": "ir.actions.act_window_close"}

    # END #######
