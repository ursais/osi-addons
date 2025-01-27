# Import Odoo libs
from odoo import fields, models


class SaleOrderLine(models.Model):
    """
    Extend sale.order.line with additional fields
    """

    _inherit = "sale.order.line"

    # COLUMNS ##########

    locked = fields.Boolean(
        string="Locked",
        related="order_id.locked",
    )

    # END ##########
