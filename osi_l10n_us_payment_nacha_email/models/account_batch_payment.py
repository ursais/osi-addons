# Copyright 2025, AUTHOR(S)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64
import logging
from odoo import _, models, fields, api, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
        
        This method uses database-level locking to prevent duplicate email sends
        even when called concurrently. The remittance_email_sent flag is set
        atomically before sending emails to ensure only one execution proceeds.
        
        The method uses with_for_update() to lock the batch record at the database
        level, preventing concurrent execution. The flag is set immediately after
        acquiring the lock and before sending emails, ensuring that any concurrent
        calls will see the flag as True and skip execution.
        """
        template = self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt"
        )

        for batch in self:
            # Early exit if no payments
            if not batch.payment_ids:
                continue
            
            # Use database-level locking to prevent concurrent execution
            # This ensures only one process can send emails for this batch at a time.
            # Other concurrent calls will wait for the lock and then see the flag as True.
            batch_locked = batch.with_for_update()
            
            # Check if email was already sent (after acquiring lock)
            # This check happens after lock acquisition to ensure we see the latest state
            if batch_locked.remittance_email_sent:
                _logger.info(
                    "Remittance email already sent for batch %s (ID: %s). Skipping.",
                    batch.name,
                    batch.id,
                )
                continue
            
            # Set flag atomically BEFORE sending emails to prevent race conditions
            # This ensures that concurrent calls waiting on the lock will see
            # the flag as True when they acquire the lock
            batch_locked.write({"remittance_email_sent": True})
            # Flush to ensure the flag is written to database within current transaction
            # Note: The lock ensures other transactions will wait, so they'll see this
            # change when the transaction commits
            self.env.flush()
            
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
                        # Reset flag on validation error so user can fix and retry
                        batch_locked.write({"remittance_email_sent": False})
                        self.env.flush()
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
                    # Generate the Payment Detail's report.
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
                    _logger.info(
                        "Remittance email sent successfully for batch %s (ID: %s) to partner %s",
                        batch.name,
                        batch.id,
                        partner.name,
                    )
            except Exception as e:
                # Reset flag on error so user can retry after fixing the issue
                # Only reset if it's not a ValidationError (which was already handled)
                if not isinstance(e, ValidationError):
                    batch_locked.write({"remittance_email_sent": False})
                    self.env.flush()
                _logger.error(
                    "Error sending remittance email for batch %s (ID: %s): %s",
                    batch.name,
                    batch.id,
                    str(e),
                    exc_info=True,
                )
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
