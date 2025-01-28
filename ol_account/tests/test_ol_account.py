from odoo.tests import common, tagged
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestAutoInvoiceOnDelivery(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.config_param = cls.env["ir.config_parameter"].sudo()
        cls.sale_order_model = cls.env["sale.order"]
        cls.stock_picking_model = cls.env["stock.picking"]
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "invoice_policy": "delivery",
                "type": "product",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.sale_order = cls.sale_order_model.create(
            {
                "partner_id": cls.partner.id,
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
