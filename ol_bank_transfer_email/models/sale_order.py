# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """Add new field to Sale Order."""

    _inherit = "sale.order"

    # METHOD #####

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            template = order.sale_payment_method_id.sale_email_template_id
            if template:
                template.send_mail(order.id, force_send=True)
        return res

    # END #########
