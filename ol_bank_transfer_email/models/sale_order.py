# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Add new field to Sale Order."""

    _inherit = "sale.order"

    # COLUMNS #####

    payment_method_mail_send = fields.Boolean(copy=False)

    # END #########
    # METHOD #####

    # Exceptions that are "ok" and should not block email sending
    ALLOWED_EXCEPTIONS = [
        "ol_sale.exception_so_bank_tranfer_payment",
    ]

    def write(self, vals):
        """Override write to send email if no blocking exceptions."""
        res = super().write(vals)
        order_review = self.env.ref(
            "ol_sale_substate.base_substate__order_review", raise_if_not_found=True
        )

        for order in self.filtered(
            lambda l: not l.payment_method_mail_send
            and l.substate_id.id == order_review.id
            and l.sale_payment_method_id.sale_email_template_id
        ):
            rule_ids = order.detect_exceptions() or []

            # Browse the exception rules
            rules = self.env["exception.rule"].browse(rule_ids)

            # Map rule_id -> xml_id
            xml_ids_map = rules.get_external_id()

            # Check which rules are NOT in whitelist
            blocking = [
                r_id
                for r_id in rule_ids
                if xml_ids_map.get(r_id) not in self.ALLOWED_EXCEPTIONS
            ]

            if not blocking:
                template = order.sale_payment_method_id.sale_email_template_id
                template.send_mail(order.id, force_send=True)
                order.write({"payment_method_mail_send": True})

        return res

    # END #########
