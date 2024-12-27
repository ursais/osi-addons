from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_note = fields.Text(
        string="Delivery Note",
        related="sale_id.delivery_note",
        store=True
    )
