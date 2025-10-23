from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleBankTranfer(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.customer = cls.env.ref("hr.work_contact_mit")
        cls.product = cls.env.ref("product.product_product_6")
        cls.product_a = cls.env.ref("product.product_product_10")
        cls.product_a.invoice_policy = "order"
        cls.payment_method = cls.env["payment.method"].create(
            {
                "name": "Bank",
                "code": "BNK",
                "sale_email_template_id": cls.env.ref(
                    "ol_bank_transfer_email.customer_bank_transfer_email_template"
                ).id,
            }
        )

    def test_sale_order_confirm(self):
        # Create a sale order with necessary details
        # Count mail.mail records before
        before_count = self.env["mail.mail"].sudo().search_count([])
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "original_commitment_date": "2025-04-24",
                "commitment_date": "2025-05-30",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "override_saleable_exception": True,
                "sale_payment_method_id": self.payment_method.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product_a.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product_a.uom_id.id,
                            "price_unit": self.product_a.list_price,
                        },
                    )
                ],
            }
        )

        # Confirm the sale order
        sale_order.action_confirm()
        after_count = self.env["mail.mail"].sudo().search_count([])
        self.assertNotEqual(
            after_count,
            before_count,
            "Expected one email to be created on confirmation.",
        )
