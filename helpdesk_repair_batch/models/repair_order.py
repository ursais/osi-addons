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
