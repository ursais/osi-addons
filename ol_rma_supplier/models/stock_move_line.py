from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move.line"

    rma_line_id = fields.Many2one(
        related="move_id.rma_line_id",
        string="RMA Line",
        store=True,
    )
