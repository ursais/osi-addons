# Import Odoo libs
from odoo import fields, models


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

    def _action_repair_confirm(self):
        """
        This is called with confirm wizard when qty is less than zero.
        We want to trigger the _update_batch_state after
        """
        res = super()._action_repair_confirm()
        if self.repair_batch_id:
            self.repair_batch_id._update_batch_state()
        return res

    # END #######
