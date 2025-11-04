# Import Odoo libs
from odoo import _,api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # COLUMNS ###

    repair_batch_id = fields.Many2one(
        comodel_name="repair.batch",
        string="Repair Batch",
        ondelete="set null",
    )
    part_lines = fields.One2many(
        comodel_name="repair.batch.line",
        inverse_name="repair_batch_id",
        string="Parts",
    )
    show_create_removal_button = fields.Boolean(
        compute="_compute_show_create_removal_button",
    )

    # END #######
    # METHODS ###

    @api.depends("move_ids")
    def _compute_show_create_removal_button(self):
        for rec in self:
            rec.show_create_removal_button = not rec.move_ids

    def open_repair_full_form(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.order",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def _action_repair_confirm(self):
        """
        This is called with confirm wizard when qty is less than zero.
        We want to trigger the _update_batch_state after
        """
        res = super()._action_repair_confirm()
        if self.repair_batch_id:
            self.repair_batch_id._update_batch_state()
        return res

    def action_create_removal_lines(self):
        self.ensure_one()
        if not self.lot_id:
            raise ValidationError(_("Please set a Serial Number on this repair order."))

        if self.move_ids:
            return True

        ComponentHistory = self.env["component.history"]

        history_lines = ComponentHistory.search(
            [
                ("lot_id", "=", self.lot_id.id),
                ("invisible", "=", False),
            ]
        )

        new_moves = []
        for history in history_lines:
            new_moves.append(
                (
                    0,
                    0,
                    {
                        "repair_line_type": "remove",
                        "product_id": history.product_id.id,
                        "lot_ids": (
                            history.component_lot_ids.ids
                            if history.component_lot_ids
                            else False
                        ),
                        "product_uom_qty": history.qty_changed,
                        "repair_id": self.id,
                        "location_id": self.location_id.id,
                        "location_dest_id": self.parts_location_id.id,
                    },
                )
            )

        if new_moves:
            self.write({"move_ids": new_moves})

    def write(self, vals):
        """
        If the repair state is changing we want to make sure the batch
        state is also updated.
        """
        res = super().write(vals)

        # Check if the state is changing
        if "state" in vals:
            for order in self:
                if order.repair_batch_id:
                    # Trigger the _update_batch_state method on the batch
                    order.repair_batch_id._update_batch_state()

        return res

    # END #######
