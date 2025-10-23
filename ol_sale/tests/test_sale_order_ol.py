from odoo.exceptions import ValidationError
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.customer = cls.env.ref("hr.work_contact_mit")
        cls.product = cls.env.ref("product.product_product_6")
        cls.product_a = cls.env.ref("product.product_product_10")
        cls.product_a.invoice_policy = "order"

    def test01_action_confirm_ValidationError(self):
        """
        Test to ensure that Validation Error is raised
        when original request date is missing
        """
        # Without original_commitment_date
        sale_wo_original_commitment_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "pricelist_id": self.customer.property_product_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        # With original_commitment_date
        sale_w_original_commitment_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "original_commitment_date": "2024-06-12",
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(ValidationError):
            sale_wo_original_commitment_date.action_confirm()
        try:
            sale_w_original_commitment_date.action_confirm()
        except ValidationError:
            self.fail("action_confirm() raised ValidationError unexpectedly!")

        # Assert the sale order was confirmed
        self.assertEqual(sale_w_original_commitment_date.state, "sale")

    def test02_sale_order_confirm(self):
        # Create a sale order with necessary details
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "original_commitment_date": "2024-06-12",
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "override_saleable_exception": True,
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

        sale_order.action_confirm()
        self.assertEqual(sale_order.state, "sale", "Sale order should be confirmed.")

        invoice = sale_order._create_invoices()
        self.assertTrue(invoice, "Invoice should be created.")
        self.assertEqual(
            invoice.move_type, "out_invoice", "Invoice should be a customer invoice."
        )

        # Send confirmation email
        wizard = (
            self.env["forward.confirmation.email.wizard"]
            .with_context({"active_model": "sale.order", "active_id": sale_order.id})
            .create({"recipients": self.customer.email})
        )
        wizard.forward_confirmation_email()

        # Validate picking
        for picking in sale_order.picking_ids:
            picking.button_validate()
            self.assertEqual(picking.state, "done", "Picking should be done.")
            picking.send_customer_emails()

        self.assertTrue(sale_order.picking_ids, "Pickings should be created.")
