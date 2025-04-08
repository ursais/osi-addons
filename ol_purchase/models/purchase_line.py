# Import Odoo Libs
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    """
    Update purchase order lines with fields
    """

    _inherit = "purchase.order.line"

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # END #########
