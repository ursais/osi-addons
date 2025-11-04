# Copyright 2025, AUTHOR(S)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64
from odoo import _, models, fields, api, Command
from odoo.exceptions import ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    auto_send_email = fields.Boolean(string="Auto Send Remittance Email", default=True)
    remittance_email_sent = fields.Boolean(string="Email Send")

    def _get_ap_contact_email(self, payment):
        """
        Returns the AP contact email from the payment.ap_partner_id.
        Raises an error if missing.
        """
        if not payment.ap_partner_id:
            raise ValidationError(
                _("AP contact not set on payment %s (Partner: %s).")
                % (payment.name, payment.partner_id.display_name)
            )

        if not payment.ap_partner_id.email:
            raise ValidationError(
                _("AP contact on payment %s (Partner: %s) has no email.")
                % (payment.name, payment.partner_id.display_name)
            )

        return payment.ap_partner_id.email

    def action_send_detailed_payment_emails(self):
        """
        Sends remittance emails to AP contacts per partner for this batch.
        Validates presence of AP contact and email.
        Ensures emails are only sent once by setting the flag immediately after check.
        """
        template = self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt"
        )

        for batch in self:
            if not batch.payment_ids:
                continue
            if batch.remittance_email_sent:
                continue
            
            # Set flag immediately after check to prevent race conditions
            # This ensures that even if _generate_export_file is called multiple times,
            # only the first call will proceed to send emails
            batch.write({"remittance_email_sent": True})
            
            # Group payments by partner
            partner_groups = {}
            for payment in batch.payment_ids:
                partner = payment.partner_id
                partner_groups.setdefault(partner, []).append(payment)

            for partner, payments in partner_groups.items():
                # Use first payment to get ap_partner_id (assuming same AP contact per partner)
                email_to = None
                for payment in payments:
                    try:
                        email_to = self._get_ap_contact_email(payment)
                        break  # Take the first valid one
                    except ValidationError as e:
                        continue
                if not email_to:
                    raise ValidationError(
                        _(
                            "No valid AP contact email found for partner: %s in batch: %s"
                        )
                        % (partner.display_name, batch.name)
                    )

                amount_total = sum([pay.amount for pay in payments])
                report_action = self.env.ref(
                    "osi_l10n_us_payment_nacha_email.action_report_detailed_payment_receipt"
                )
                # generated the Payment Detail's report.
                report = report_action._render_qweb_pdf(
                    report_ref="osi_l10n_us_payment_nacha_email.action_report_detailed_payment_receipt",
                    res_ids=[p.id for p in payments],
                )
                filename = batch.name + ".pdf"
                payment_attachment = self.env["ir.attachment"].create(
                    {
                        "name": filename,
                        "type": "binary",
                        "datas": base64.b64encode(report[0]),
                        # "store_fname": filename,
                        "mimetype": "application/x-pdf",
                    }
                )
                # Send the email
                template.with_context(
                    {
                        "partner_name": partner.name,
                        "batch_name": batch.name,
                        "amount_total": amount_total,
                    }
                ).send_mail(
                    batch.id,
                    force_send=True,
                    email_values={
                        "email_to": email_to,
                        "attachment_ids": [Command.set(payment_attachment.ids)],
                    },
                )

    def _generate_export_file(self):
        data = super()._generate_export_file()
        if (
            self.auto_send_email
            and not self.remittance_email_sent
            and self.payment_method_code == "nacha"
        ):
            self.action_send_detailed_payment_emails()

        return data
