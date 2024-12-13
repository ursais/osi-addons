from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_out_id = fields.Many2one(
        "rma.supplier.order",
        string="RMA Out",
    )
    rma_in_id = fields.Many2one(
        "rma.supplier.order",
        string="RMA In",
    )
