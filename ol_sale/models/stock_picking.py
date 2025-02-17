# Import Odoo libs
from odoo import fields, models


class StockPicking(models.Model):
    """Add new field to Pickings."""

    _inherit = "stock.picking"

    # COLUMNS #####

    delivery_note = fields.Text(
        string="Delivery Note",
        related="sale_id.delivery_note",
        store=True,
    )

    # END #########
