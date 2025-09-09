# Import Odoo libs
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Add new field to Sale Order."""

    _inherit = "sale.order"

    # COLUMNS #####

    payment_method_mail_send = fields.Boolean(copy=False)
    allow_quote_payment = fields.Boolean(
        related="sale_payment_method_id.allow_quote_payment",
        help="Helper field for form view to show the create down payment invoice button",
    )

    # END #########
    # METHOD #####

    def write(self, vals):
        """
        Override write to send email if pay method has template.
        Sent in order review substate.
        """
        res = super().write(vals)
        order_review = self.env.ref(
            "ol_sale_substate.base_substate__order_review", raise_if_not_found=True
        )

        for order in self.filtered(
            lambda l: not l.payment_method_mail_send
            and l.substate_id.id == order_review.id
            and l.sale_payment_method_id.sale_email_template_id
        ):
            template = order.sale_payment_method_id.sale_email_template_id
            template.send_mail(order.id, force_send=True)
            order.write({"payment_method_mail_send": True})

        return res

    def action_confirm(self):
        """
        Inherit confirm method to prevent confirmation if bank transfer is pay method and
        exception is not ignored.
        """
        # Get Bank Payment Exception
        exception = self.env.ref(
            "ol_bank_transfer_email.exception_so_bank_tranfer_payment",
            raise_if_not_found=True,
        )

        # Check if bank transfer payment method is set, SO is not fully paid and
        # bank transfer exception isn't active or ignored.
        for rec in self:
            if (
                rec.sale_payment_method_id
                and "Bank Transfer" in rec.sale_payment_method_id.name
                and exception not in rec.exception_ids
                and exception not in rec.ignored_exception_ids.exception_rule_id
                and rec.invoice_status != "full paid"
            ):
                raise ValidationError(
                    _(
                        "The Quotation is set for Bank Transfer and full payment has not been received so it cannot be confirmed."
                        " Please move the quote to 'Quotation Sent' status and receive payment before trying to confirm."
                    )
                )

        return super().action_confirm()

    # END #########
