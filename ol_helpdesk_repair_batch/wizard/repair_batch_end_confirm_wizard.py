from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairBatchEndConfirmWizard(models.TransientModel):
    _name = "repair.batch.end.confirm.wizard"
    _description = "Confirm Repair Quantity Differences"

    batch_id = fields.Many2one(
        comodel_name="repair.batch",
        string="Batch",
        readonly=True,
    )
    repair_ids = fields.Many2many(
        comodel_name="repair.order",
        string="Repairs to Confirm",
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name="repair.batch.end.confirm.line",
        inverse_name="wizard_id",
        string="Differences",
        copy=False,
    )

    @api.onchange("batch_id", "repair_ids")
    def _onchange_batch_repairs(self):
        if self.batch_id:
            self.repair_ids = self.batch_id.repair_ids.filtered(
                lambda r: r.state not in ("done", "cancel")
            )

            lines = []
            for line in self.repair_ids.move_ids.filtered(
                lambda m: m.repair_line_type == "add"
                and m.product_uom_qty != m.quantity
                and m.state not in ("done", "cancel")
            ):
                lines.append(
                    (
                        0,
                        0,
                        {
                            "wizard_id": self.id,
                            "move_id": line.id,
                            "product_id": line.product_id.id,
                            "demand_qty": line.product_uom_qty,
                            "used_qty": line.quantity,
                            "repair_id": line.repair_id.id,
                        },
                    )
                )

            self.line_ids = lines

    def action_apply_and_end_repairs(self):
        if not self.line_ids:
            raise UserError("No lines to process.")

        # Update all moves first
        for line in self.line_ids:
            move = line.move_id
            if move:
                move.write(
                    {
                        "quantity": line.used_qty,
                        "product_uom_qty": line.demand_qty,
                    }
                )

        # Get all repairs affected by these lines
        repairs = self.repair_ids
        if not repairs:
            repairs = self.env["repair.order"].browse(
                self.line_ids.mapped("repair_id.id")
            )

        # Attempt to end repairs
        for repair in repairs:
            try:
                repair.action_repair_end()
            except UserError as e:
                # Show a message to the user instead of silently failing
                raise UserError(f"Failed to end repair {repair.display_name}: {e}")

        self.batch_id._update_batch_state()
        return {"type": "ir.actions.act_window_close"}


class RepairBatchEndConfirmLine(models.TransientModel):
    _name = "repair.batch.end.confirm.line"
    _description = "Repair Difference Summary Line"

    wizard_id = fields.Many2one(
        "repair.batch.end.confirm.wizard", required=True, ondelete="cascade"
    )
    repair_id = fields.Many2one("repair.order", string="Repair", readonly=True)
    move_id = fields.Many2one("stock.move", string="Part Line (Move)", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    demand_qty = fields.Float(string="Demand (Expected)")
    used_qty = fields.Float(
        string="Actually Used", help="Editable — set the true used quantity"
    )
    difference = fields.Float(
        string="Difference",
        compute="_compute_difference",
        store=False,
    )

    @api.depends("demand_qty", "used_qty")
    def _compute_difference(self):
        for line in self:
            line.difference = (line.used_qty or 0.0) - (line.demand_qty or 0.0)
