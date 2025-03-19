# Import Odoo libs
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestBackorderEmail(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Environment references to models
        cls.SaleOrder = cls.env["sale.order"]
        cls.ResPartner = cls.env["res.partner"]
        cls.ProductObj = cls.env["product.product"]
        cls.IrConfigParam = cls.env["ir.config_parameter"]

        # Enable backorder email setting by default
        cls.IrConfigParam.sudo().set_param("sale.enable_backorder_email", "True")

        # Create a product that allows backorders
        cls.product = cls.ProductObj.create(
            {
                "name": "Large Cabinet",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "allow_backorder": True,  # Enable backorder for this product
                "type": "product",  # Storable product
                "qty_available": 0,  # Ensure it is out of stock
            }
        )

        # Create a dummy partner to use in sale orders
        cls.partner = cls.ResPartner.create({"name": "Dummy Partner"})

    def test01_backorder_email_enabled(self):
        """Test that the backorder email is sent when the setting is enabled."""
        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,  # Operation to create a new record
                        0,  # No existing record to modify
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        # Ensure the global setting is enabled
        self.assertTrue(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale.enable_backorder_email")
            == "True"
        )

        # Check that the computed field reflects the setting
        self.assertTrue(sale_order.enable_backorder_email)

        # Ensure that the sale order is initially set to send a backorder email
        self.assertTrue(sale_order.to_send_backorder_email)

        # Confirm the sale order, which should trigger the backorder email
        sale_order.action_confirm()

        # Verify that the backorder email flag is cleared after sending
        self.assertFalse(sale_order.to_send_backorder_email)

    def test02_backorder_email_disabled(self):
        """Test that the backorder email is NOT sent when the setting is disabled."""
        # Disable the global setting
        self.env["ir.config_parameter"].sudo().set_param(
            "sale.enable_backorder_email", "False"
        )

        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        # Ensure the setting is disabled
        self.assertFalse(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale.enable_backorder_email")
            == "True"
        )

        # Check that the computed field reflects the setting
        self.assertFalse(sale_order.enable_backorder_email)

        # Confirm the sale order
        sale_order.action_confirm()

        # Ensure the email flag is still True (it was not sent)
        self.assertTrue(sale_order.to_send_backorder_email)
