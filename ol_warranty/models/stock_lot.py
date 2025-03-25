# Import Odoo libs
from odoo import fields, models


class StockLot(models.Model):
    """Add warranty fields to Serial/Lot."""

    _inherit = "stock.lot"

    # COLUMNS ###

    warranty_expiration_date = fields.Date(
        string="Warranty Expiration Date",
        tracking=True,
        help="Warranty expires on this date.",
    )

    # END #######
