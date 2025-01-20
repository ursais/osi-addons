# Import Odoo libs
from odoo import fields, models


class StockMoveLine(models.Model):
    """Inherit Stock Move Line to link line back to RMA Line."""

    _inherit = "stock.move.line"

    # COLUMNS ######

    rma_supplier_line_id = fields.Many2one(
        related="move_id.rma_supplier_line_id",
        string="RMA Line",
        store=True,
    )

    # END ##########
