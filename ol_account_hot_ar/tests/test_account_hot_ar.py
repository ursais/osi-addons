# Import Odoo libs
from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestAccountHotAR(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.browse_ref("base.main_company")

        # ==== Partners ====
        self.partner_a = self.env["res.partner"].create(
            {
                "name": "partner_a",
            }
        )

        # ==== Products ====
        self.product_a = self.env["product.product"].create(
            {
                "name": "product_a",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "lst_price": 1000.0,
                "standard_price": 800.0,
                "taxes_id": [Command.set(self.company.account_sale_tax_id.ids)],
                "supplier_taxes_id": [
                    Command.set(self.company.account_purchase_tax_id.ids)
                ],
            }
        )

        # ==== Invoice ====
        self.invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.from_string("2024-01-01"),
                "currency_id": self.company.currency_id.id,
                "hot_ar": True,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 3,
                            "price_unit": 750,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 3000,
                        }
                    ),
                ],
            }
        )

    def test00_validate_hot_ar_grace_period(self):
        with self.assertRaises(ValidationError):
            self.company.write({"hot_ar_grace_period": -10})

    def test01_hot_ar_grace_period(self):
        self.invoice.action_post()
        self.assertTrue(self.invoice.payment_state in ("not_paid"))
        self.assertTrue(self.invoice.hot_ar)
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({})._create_payments()
        self.assertTrue(self.invoice.payment_state in ("paid", "in_payment"))
        self.invoice.onchange_payment_state()
        self.assertFalse(self.invoice.hot_ar)

    def test02_update_hot_ar_invoices(self):
        self.invoice.invoice_date_due = self.invoice.invoice_date
        self.invoice.hot_ar = False
        self.invoice.action_post()
        self.assertFalse(self.invoice.partner_id.hot_ar)
        self.env["account.move"]._update_hot_ar_invoices()
        self.assertTrue(self.invoice.partner_id.hot_ar)
