# Import Odoo libs
from odoo import models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    def action_compute_esd(self):
        for order in self:
            order.line_ids._compute_customer_lead()
