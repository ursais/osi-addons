# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Add new field to Sale Order."""

    _inherit = "sale.order"

    # COLUMNS #####

    payment_method_mail_send = fields.Boolean(copy=False)

    # END #########
    # METHOD #####

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.detect_exceptions() and not order.payment_method_mail_send:
                template = order.sale_payment_method_id.sale_email_template_id
                if template:
                    template.send_mail(order.id, force_send=True)
                    # Updated boolean to avoid sending multiple emails in
                    # case of multiple time of calling 'action_confirm'
                    order.payment_method_mail_send = True
        return res

    # END #########
