# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    blanket_order_id2 = fields.Many2one(
        "sale.blanket.order",
        string="Origin blanket order2",
    )
