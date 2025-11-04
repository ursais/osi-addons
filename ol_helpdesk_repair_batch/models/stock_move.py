# Import Odoo libs
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # COLUMNS ###

    repair_batch_line_id = fields.Many2one(
        comodel_name="repair.batch.line",
        string="Repair Batch Line",
        ondelete="cascade",
    )

    # END #######
