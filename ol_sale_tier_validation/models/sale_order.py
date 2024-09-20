from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "tier.validation"]

    _state_from = ["draft"]
    _state_to = ["sent", "sale"]
