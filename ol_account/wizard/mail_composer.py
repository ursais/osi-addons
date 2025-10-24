from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.depends(
        "composition_mode", "model", "parent_id", "res_domain", "res_ids", "template_id"
    )
    def _compute_partner_ids(self):
        super()._compute_partner_ids()
        for composer in self:
            if self._context.get("active_model") == "account.payment":
                account_payments = self.env["account.payment"].browse(
                    self._context.get("active_ids")
                )
                for payment in account_payments:
                    if payment.payment_type == "outbound":
                        ar_contacts = self.env["res.partner"].search(
                            [
                                ("ar", "=", True),
                                ("id", "child_of", payment.partner_id.id),
                            ]
                        )
                        if not ar_contacts:
                            raise UserError(
                                _(
                                    """No ‘AR’ contacts are found for %s, """
                                    """please add or set the ‘AR’ setting on a contact and try again.""", payment.partner_id.display_name
                                )
                            )
                        composer.partner_ids = ar_contacts.ids

                    if payment.payment_type == "inbound":
                        ap_contacts = self.env["res.partner"].search(
                            [
                                ("ap", "=", True),
                                ("id", "child_of", payment.partner_id.id),
                            ]
                        )
                        if not ap_contacts:
                            raise UserError(
                                _(
                                    """No ‘AP’ contacts are found for %s, """
                                    """please add or set the ‘AP’ setting on a contact and try again.""", payment.partner_id.display_name
                                )
                            )
                        composer.partner_ids = ap_contacts.ids

