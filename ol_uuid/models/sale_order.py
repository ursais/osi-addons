# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """
    Add UUID compatibility
    """

    _name = "sale.order"
    _inherit = ["sale.order", "res.uuid"]


class SaleOrderLine(models.Model):
    """
    Add UUID compatibility
    """

    _name = "sale.order.line"
    _inherit = ["sale.order.line", "res.uuid"]
