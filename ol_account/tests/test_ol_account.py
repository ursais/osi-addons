from odoo.tests import common, tagged
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo import fields


@tagged("-at_install", "post_install")
class TestAutoInvoiceOnDelivery(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.config_param = cls.env["ir.config_parameter"].sudo()
        cls.sale_order_model = cls.env["sale.order"]
        cls.stock_picking_model = cls.env["stock.picking"]
        cls.payment_method_id = cls.env["payment.method"].search([], limit=1)
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "invoice_policy": "delivery",
                "type": "product",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "sale_payment_method_id": cls.payment_method_id.id,
            }
        )
        cls.invoice_partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner Invoice",
                "type": "invoice",
                "parent_id": cls.partner.id,
            }
        )

        cls.sale_order = cls.sale_order_model.create(
            {
                "partner_id": cls.partner.id,
                "override_saleable_exception": True,
                "original_commitment_date": fields.Datetime.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        cls.sale_order._onchange_partner_invoice_id_payment_method()

        # Create a storable product
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "detailed_type": "product",  # Storable product
                "list_price": 100.0,
                "ship_ok": True,
            }
        )
        location_id = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_1, location_id, 500
        )

        # Create a sale order
        cls.sale_order_1 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "override_saleable_exception": True,
                "original_commitment_date": fields.Datetime.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_1.id,
                            "product_uom_qty": 1,
                            "price_unit": cls.product.list_price,
                        },
                    )
                ],
            }
        )

    def test_payment_method(self):
        "Test the partner Payment method on sale order"
        self.assertEqual(
            self.sale_order.sale_payment_method_id.id, self.payment_method_id.id
        )

    def test_auto_invoice_on_delivery(self):
        """Test auto-invoice creation on delivery validation."""
        # Enable configuration parameters
        self.config_param.set_param(
            "ol_account.auto_create_invoice_delivery_validate", True
        )
        self.config_param.set_param(
            "ol_account.auto_post_invoice_delivery_validate", True
        )

        # Confirm the sale order
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids

        # Validate delivery
        picking.move_ids.write({"quantity": 1})
        picking.button_validate()

        # Check that the invoice is created and posted
        invoice = self.sale_order.invoice_ids
        self.assertTrue(invoice, "Invoice should be created on delivery validation.")
        self.assertEqual(
            invoice.state, "posted", "Invoice should be posted automatically."
        )

    def test_auto_bill_on_receipt(self):
        """Test auto-bill creation on receipt validation."""

        # Enable configuration parameters
        self.config_param.set_param(
            "ol_account.auto_create_bill_receipt_validate", True
        )
        self.config_param.set_param("ol_account.auto_post_bill_receipt_validate", True)

        # Create a purchase order with a storable product
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "product_qty": 1.0,
                            "product_uom": self.product_1.uom_id.id,
                            "price_unit": self.product_1.list_price,
                            "date_planned": fields.Datetime.today(),
                        },
                    )
                ],
            }
        )

        purchase_order.button_confirm()
        picking = purchase_order.picking_ids
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = 1.0
        picking.button_validate()

        # Check that the bill is created and posted
        bill = purchase_order.invoice_ids
        self.assertTrue(bill, "Bill should be created on receipt validation.")
        self.assertEqual(bill.state, "posted", "Bill should be posted automatically.")

    def test_restrict_account_move_deletion(self):
        """Test restriction on account.move deletion."""
        account_move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
            }
        )
        # Try deleting as a regular user
        with self.assertRaises(UserError):
            account_move.with_user(2).unlink()

        # Ensure deletion is allowed for the system admin (user ID = 1)
        self.env.uid = 1
        account_move.unlink()

        # Assert that the account_move was unlinked
        self.assertFalse(
            self.env["account.move"].search([("id", "=", account_move.id)])
        )

    def test_res_config_settings(self):
        """Test the settings model fields."""
        settings = self.env["res.config.settings"].create(
            {
                "auto_create_invoice_delivery_validate": True,
                "auto_post_invoice_delivery_validate": True,
            }
        )
        settings.execute()

        # Check that the config parameters are updated
        self.assertTrue(
            self.config_param.get_param(
                "ol_account.auto_create_invoice_delivery_validate"
            ),
            "Auto create invoice on delivery setting should be saved.",
        )
        self.assertTrue(
            self.config_param.get_param(
                "ol_account.auto_post_invoice_delivery_validate"
            ),
            "Auto post invoice on delivery setting should be saved.",
        )

    def test_sale_order_downpayment(self):
        # Confirm Sale Order
        self.sale_order_1.action_confirm()
        self.assertEqual(self.sale_order_1.state, "sale", "Sale Order not confirmed")
        so_context = {
            "active_model": "sale.order",
            "active_ids": [self.sale_order_1.id],
            "active_id": self.sale_order_1.id,
            # 'default_journal_id': self.company_data['default_journal_sale'].id,
        }
        # Register 20% Down Payment
        downpayment_20 = (
            self.env["sale.advance.payment.inv"]
            .with_context(so_context)
            .create(
                {
                    "advance_payment_method": "percentage",
                    "amount": 20.0,
                }
            )
        )
        downpayment_20.create_invoices()

        # Register 10% Down Payment
        downpayment_10 = (
            self.env["sale.advance.payment.inv"]
            .with_context(so_context)
            .create(
                {
                    "advance_payment_method": "percentage",
                    "amount": 10.0,
                }
            )
        )
        downpayment_10.create_invoices()
        self.sale_order_1.invoice_ids.action_post()
        downpayment_ids = self.sale_order_1.invoice_ids
        # Confirm Delivery
        picking = self.sale_order_1.picking_ids.filtered(lambda p: p.state != "done")
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        self.assertEqual(picking.state, "done", "Delivery not confirmed")

        # Create Final Invoice
        invoice_wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(so_context)
            .create({"advance_payment_method": "delivered"})
        )
        invoice_wizard.create_invoices()
        invoice = self.sale_order_1.invoice_ids.filtered(
            lambda inv: inv.state != "cancel"
        )
        invoice.action_post()

        self.assertEqual(
            invoice.state, "posted", "Final Invoice not created and posted"
        )
