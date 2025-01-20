# Import Odoo libs
from odoo import fields, models


class StockMove(models.Model):
    """Inherit Stock Move to link line back to RMA Line."""

    _inherit = "stock.move"

    # COLUMNS ######

    rma_supplier_line_id = fields.Many2one(
        "rma.supplier.order.line",
        string="RMA Line",
    )
    rma_note = fields.Text(
        string="RMA Note",
        related="rma_supplier_line_id.note",
        store=True,
    )

    # END ##########
