# Import Odoo libs
from odoo import api, fields, models


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

    # END #######
    # METHODS ###

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
