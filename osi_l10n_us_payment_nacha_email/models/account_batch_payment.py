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
        
        Uses SQL-level atomic update to check and set the remittance_email_sent flag
        atomically in a single database operation to prevent duplicate email sends when
        called concurrently from multiple sources (e.g., _generate_export_file
        and manual button clicks).
        """
        template = self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt"
        )

        for batch in self:
            if not batch.payment_ids:
                continue
            
            # Use SQL-level atomic update to check and set flag in one operation
            # This prevents race conditions by ensuring only one transaction can
            # successfully update the flag from False to True
            self.env.cr.execute(
                """
                UPDATE account_batch_payment
                SET remittance_email_sent = TRUE
                WHERE id = %s AND remittance_email_sent = FALSE
                RETURNING id
                """,
                (batch.id,)
            )
            
            # If no row was updated, it means the flag was already True
            if not self.env.cr.fetchone():
                continue
            
            # Invalidate cache to reflect the database change
            batch.invalidate_recordset(['remittance_email_sent'])
            
            try:
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
                        # Reset flag if we can't send emails due to missing contact
                        batch.write({"remittance_email_sent": False})
                        self.env.flush_all()
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
            except Exception:
                # If an error occurs during email sending, reset the flag
                # so the user can retry. This prevents being stuck in a state
                # where emails were partially sent but the flag is set.
                batch.write({"remittance_email_sent": False})
                self.env.flush_all()
                raise

    def _generate_export_file(self):
        data = super()._generate_export_file()
        if (
            self.auto_send_email
            and not self.remittance_email_sent
            and self.payment_method_code == "nacha"
        ):
            self.action_send_detailed_payment_emails()

        return data
