# Import Odoo libs
from odoo import fields, models


class StockPickingType(models.Model):
    """Inherit operation types to add unreserve on create option."""

    _inherit = "stock.picking.type"

    # COLUMNS #####

    unreserve_on_create = fields.Boolean(
        string="Disable Auto Reserve on Confirm",
        help="If checked, stock moves will be not be reserved automatically "
        "when the receipt is confirmed.",
    )

    # END #########
