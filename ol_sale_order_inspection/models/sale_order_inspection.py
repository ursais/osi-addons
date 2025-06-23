# Import Odoo libs
from odoo import fields, models


class SaleOrderInspection(models.Model):
    """New object that allow users to add inspections to orders to hold the order."""

    _name = "sale.order.inspection"
    _description = "Sale Order Inspection"

    # COLUMNS ##########

    name = fields.Char(
        string="Inspection Name",
        required=True,
    )
    group_ids = fields.Many2many(
        comodel_name="res.groups",
        string="Security Groups",
        help="When set, only the selected groups can add/remove the inspection.",
    )
    color = fields.Integer(string="Color")

    # END ##########
