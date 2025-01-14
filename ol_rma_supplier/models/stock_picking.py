# Import Odoo libs
from odoo import fields, models


class StockPicking(models.Model):
    """Inherit Picking to link back to RMA."""

    _inherit = "stock.picking"

    # COLUMNS ######

    rma_out_id = fields.Many2one(
        "rma.supplier.order",
        string="RMA Out",
    )
    rma_in_id = fields.Many2one(
        "rma.supplier.order",
        string="RMA In",
    )

    # END ##########
