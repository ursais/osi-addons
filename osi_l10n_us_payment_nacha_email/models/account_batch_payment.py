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
        
        :param payment: account.payment record
        :return: str - email address
        :raises: ValidationError if AP contact or email is missing
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

    def _check_emails_already_sent(self, batch):
        """
        Checks if emails have already been sent for this batch by looking at
        mail.message records. This provides an additional safeguard beyond
        the remittance_email_sent flag.
        
        :param batch: account.batch.payment record
        :return: bool - True if emails were already sent, False otherwise
        """
        template = self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt",
            raise_if_not_found=False,
        )
        if not template:
            return False
        
        # Check if there are any mail messages sent for this batch using the template
        messages = self.env["mail.message"].search_count(
            [
                ("model", "=", "account.batch.payment"),
                ("res_id", "=", batch.id),
                ("mail_template_id", "=", template.id),
                ("message_type", "=", "email"),
            ]
        )
        return messages > 0

    def _mark_email_sending_in_progress(self, batch):
        """
        Atomically marks the batch as having emails sent in progress.
        This prevents race conditions where multiple calls try to send
        emails simultaneously.
        
        Returns True if the batch was successfully marked (not already marked),
        False if it was already marked or emails were already sent.
        
        :param batch: account.batch.payment record
        :return: bool - True if marking succeeded, False if already marked
        """
        # Use fresh read from database to check current state
        batch.refresh()
        if batch.remittance_email_sent:
            return False
        
        # Check if emails were already sent by looking at mail.message records
        if self._check_emails_already_sent(batch):
            # Mark as sent if emails exist but flag wasn't set
            batch.write({"remittance_email_sent": True})
            return False
        
        # Atomically set the flag to prevent concurrent sends
        # This write is atomic within the transaction
        batch.write({"remittance_email_sent": True})
        return True

    def action_send_detailed_payment_emails(self):
        """
        Sends remittance emails to AP contacts per partner for this batch.
        Validates presence of AP contact and email.
        
        This method includes safeguards to prevent duplicate email sending:
        1. Checks remittance_email_sent flag
        2. Verifies mail.message records to confirm emails weren't already sent
        3. Atomically sets the flag before sending to prevent race conditions
        
        :raises: ValidationError if required data is missing
        """
        template = self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt"
        )

        for batch in self:
            # Skip if no payments in batch
            if not batch.payment_ids:
                continue
            
            # Atomic check and mark - returns False if already processed
            if not self._mark_email_sending_in_progress(batch):
                continue
            
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
                        except ValidationError:
                            continue
                    
                    if not email_to:
                        # Reset flag if we can't send due to missing email
                        batch.write({"remittance_email_sent": False})
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
                    # Generate the Payment Detail's report
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
                # Reset flag on error so user can retry
                batch.write({"remittance_email_sent": False})
                raise

    def _generate_export_file(self):
        """
        Override to automatically send remittance emails after generating
        export file for NACHA payment method.
        
        :return: dict - export file data
        """
        data = super()._generate_export_file()
        if (
            self.auto_send_email
            and not self.remittance_email_sent
            and self.payment_method_code == "nacha"
        ):
            self.action_send_detailed_payment_emails()

        return data
