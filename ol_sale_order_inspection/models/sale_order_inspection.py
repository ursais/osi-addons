# Import Odoo libs
from odoo import fields, models


class SaleOrderInspection(models.Model):
    _name = "sale.order.inspection"
    _description = "Sale Order Inspection"

    # COLUMNS ##########

    name = fields.Char("Inspection Name", required=True)
    group_ids = fields.Many2many("res.groups", string="Security Groups")
    color = fields.Integer("Color")

    # END ##########
