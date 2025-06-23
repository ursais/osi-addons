# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Adding fields to Sales Order.
    """

    _inherit = "sale.order"

    # COLUMNS ##########

    order_inspection_ids = fields.Many2many(
        comodel_name="sale.order.inspection",
        string="Order Inspections",
        readonly=True,
        copy=False,
    )

    # END ##########
