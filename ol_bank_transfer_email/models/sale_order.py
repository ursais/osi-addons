# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Add new field to Sale Order."""

    _inherit = "sale.order"

    # COLUMNS #####

    payment_method_mail_send = fields.Boolean(copy=False)

    # END #########
    # METHOD #####

    def write(self, vals):
        res = super().write(vals)
        order_review = self.env.ref(
            "ol_sale_substate.base_substate__order_review", raise_if_not_found=True
        )
        for order in self.filtered(
            lambda l: not l.payment_method_mail_send
            and l.substate_id.id == order_review.id
            and l.sale_payment_method_id.sale_email_template_id
        ):
            if not order.detect_exceptions():
                template = order.sale_payment_method_id.sale_email_template_id
                template.send_mail(order.id, force_send=True)

                order.write({"payment_method_mail_send": True})
        return res

    # END #########
