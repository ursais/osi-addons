# Import Odoo libs
from odoo import models


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    # METHODS ###

    def create_sale_order(self):
        res = super().create_sale_order()
        for rec in self:
            rec.blanket_order_id.sale_blanket_booking_trigger()
        return res

    # END #######
