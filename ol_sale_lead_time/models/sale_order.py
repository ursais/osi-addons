# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_compute_esd(self):
        for order in self:
            order.order_line._compute_customer_lead()
