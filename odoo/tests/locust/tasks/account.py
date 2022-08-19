# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

import helper
from locust import task


class AccountTaskSet(helper.BaseBackendTaskSet):
    def on_start(self, *args, **kwargs):
        super(AccountTaskSet, self).on_start(*args, **kwargs)

    @task(20)
    def generate_invoice_from_task(self):
        task_id = helper.find_random_task_done(self.client)
        if not task_id:
            logging.INFO("Failed to generate Invoice -- no Task found")
            return ()
        logging.INFO("Created Invoice for task: " + task_id.name)
        return task_id.generate_invoices()

    @task(10)
    def confirm_customer_invoice(self):
        invoice_id = helper.find_random_invoice_draft(self.client)
        if not invoice_id:
            logging.INFO("Failed to confirm Invoice -- none found")
            return ()
        return invoice_id.action_invoice_open()

    @task(10)
    def register_invoice_payment(self):
        invoice_id = helper.find_random_invoice_open(self.client)
        if not invoice_id:
            logging.INFO("Failed to register Payment -- no Invoice found")
            return ()
        account_payment = self.client.env["account.payment"]
        journal_id = self.client.env["account.journal"].search(
            [("code", "ilike", "INV")], limit=1
        )
        if type(journal_id) != int:
            journal_id = journal_id.id
        journal_rec = self.client.env["account.journal"].browse(journal_id)
        pay_method = journal_rec.inbound_payment_method_ids[0]
        vals = {
            "partner_id": invoice_id.partner_id.id,
            "partner_type": "customer",
            "payment_method_id": pay_method.id,
            "payment_type": "inbound",
            "journal_id": journal_rec.id,
            "amount": invoice_id.residual,
            "communication": invoice_id.number,
        }
        payment_id = account_payment.create(vals)
        if type(payment_id) != int:
            payment_id = payment_id.id
        payment_rec = account_payment.browse(payment_id)
        invoice_lines = self.client.env["payment.invoice.line"]
        vals = {
            "payment_id": payment_rec.id,
            "invoice_id": invoice_id.id,
            "date_invoice": invoice_id.date_invoice.strftime("%Y-%m-%d"),
            "amount": invoice_id.residual,
            "amount_total": invoice_id.residual,
            "residual": invoice_id.residual,
        }
        invoice_lines.create(vals)
        return payment_rec.post()

    @task(10)
    def generate_vendor_bill_from_po(self):
        order_id = helper.find_random_purchase_order(self.client)
        if not order_id:
            logging.INFO("Failed to generate Vendor Bill -- no PO found")
            return ()
        vendor_bill = self.client.env["account.invoice"]
        today = datetime.date.today().strftime("%Y-%m-%d")
        invoice_num = "INV" + order_id.name[2:]
        vals = {
            "partner_id": order_id.partner_id.id,
            "purchase_id": order_id.id,
            "account_id": order_id.partner_id.property_account_payable_id.id,
            "date_invoice": today,
            "supplier_invoice_number": invoice_num,
            "type": "in_invoice",
            "origin": order_id.name,
        }
        bill_id = vendor_bill.create(vals)
        order_id.write({"invoice_status": "invoiced"})
        if type(bill_id) != int:
            bill_id = bill_id.id
        bill_rec = vendor_bill.browse(bill_id)
        logging.INFO("Created Vendor Bill from: " + order_id.name)
        return bill_rec.purchase_order_change()

    @task(10)
    def confirm_vendor_bill(self):
        vendor_bill = helper.find_random_vendor_bill_draft(self.client)
        if not vendor_bill:
            logging.INFO("Failed to confirm Vendor Bill -- none found")
            return ()
        return vendor_bill.action_invoice_open()

    @task(10)
    def register_vendor_payment(self):
        vendor_bill = helper.find_random_vendor_bill_open(self.client)
        if not vendor_bill:
            logging.INFO("Failed to register Payment -- no Vendor Bill found")
            return ()
        account_payment = self.client.env["account.payment"]
        journal_id = self.client.env["account.journal"].search(
            [("code", "ilike", "BILL")], limit=1
        )
        if type(journal_id) != int:
            journal_id = journal_id.id
        journal_rec = self.client.env["account.journal"].browse(journal_id)
        pay_method = journal_rec.outbound_payment_method_ids[0]
        vals = {
            "partner_id": vendor_bill.partner_id.id,
            "partner_type": "supplier",
            "payment_method_id": pay_method.id,
            "payment_type": "outbound",
            "journal_id": journal_rec.id,
            "amount": vendor_bill.residual,
            "communication": vendor_bill.number,
        }
        payment_id = account_payment.create(vals)
        if type(payment_id) != int:
            payment_id = payment_id.id
        payment_rec = self.client.env["account.payment"].browse(payment_id)
        invoice_lines = self.client.env["payment.invoice.line"]
        vals = {
            "payment_id": payment_rec.id,
            "invoice_id": vendor_bill.id,
            "date_invoice": vendor_bill.date_invoice.strftime("%Y-%m-%d"),
            "amount": vendor_bill.residual,
            "amount_total": vendor_bill.residual,
            "residual": vendor_bill.residual,
        }
        invoice_lines.create(vals)
        logging.INFO("Posted payment for: " + payment_rec.partner_id.name)
        return payment_rec.post()
