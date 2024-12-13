from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    rma_line_id = fields.Many2one(
        "rma.supplier.order.line",
        string="RMA Line",
    )
    rma_note = fields.Text(
        string="RMA Note",
        related="rma_line_id.note",
        store=True,
    )
