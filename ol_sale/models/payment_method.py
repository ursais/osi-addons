# Import Odoo libs
from odoo import models


class SaleOrderPaymentMethod(models.Model):
    _inherit = "sale.order.payment.method"

    def get_payment_method_report_data(self):
        """Get the Proforma Invoice related report data"""

        data = {}
        for method in self:
            data[method.id] = {}
            sale_order = method.order_id
            order_data = sale_order.get_report_data()
            data[method.id]['sale_order'] = order_data
        return data
