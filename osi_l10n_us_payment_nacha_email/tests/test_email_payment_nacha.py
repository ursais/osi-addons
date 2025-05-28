from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestBatchPaymentEmail(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env["res.partner"].create(
            {
                "name": "Vendor Partner",
            }
        )
        # Create a partner and AP contact with email
        self.ap_contact = self.env["res.partner"].create(
            {
                "name": "AP Contact",
                "email": "ap@example.com",
                "parent_id": self.partner.id,
                "type": "ap_address"
            }
        )

        # Create a payment associated with the partner and AP contact
        self.payment = self.env["account.payment"].create(
            {
                "partner_id": self.partner.id,
                "amount": 100.0,
                "payment_type": "outbound",
                "journal_id": self.env["account.journal"]
                .search([("name", "=", "Bank")], limit=1)
                .id,
            }
        )
        # Create the batch payment
        self.payment.action_post()
        batch_payment_action = self.payment.create_batch_payment()
        self.batch = self.env["account.batch.payment"].browse(
            batch_payment_action.get("res_id")
        )

    def test_send_detailed_payment_emails(self):
        # Before sending
        self.assertFalse(self.batch.remittance_email_sent)

        # Ensure email template and report action exist
        self.env.ref(
            "osi_l10n_us_payment_nacha_email.email_template_detailed_payment_receipt"
        )
        self.env.ref(
            "osi_l10n_us_payment_nacha_email.action_report_detailed_payment_receipt"
        )

        # Call method
        self.batch.action_send_detailed_payment_emails()

        # After sending
        self.assertTrue(self.batch.remittance_email_sent)

    def test_missing_ap_contact_raises_error(self):
        # Remove AP contact
        self.payment.ap_partner_id = False

        with self.assertRaises(ValidationError):
            self.batch.action_send_detailed_payment_emails()

    def test_missing_ap_email_raises_error(self):
        # Set AP contact without email
        self.ap_contact.email = False

        with self.assertRaises(ValidationError):
            self.batch.action_send_detailed_payment_emails()
