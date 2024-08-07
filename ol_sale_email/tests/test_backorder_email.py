# Import Odoo libs
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestProductTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        # Set up method to initialize necessary records and models for testing
        super().setUpClass()

        # Environment references to models
        cls.SaleOrder = cls.env["sale.order"]
        cls.ResPartner = cls.env["res.partner"]
        cls.ProductObj = cls.env["product.product"]

        # Create a product that allows backorders
        cls.product = cls.ProductObj.create(
            {
                "name": "Large Cabinet",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "allow_backorder": True,  # Enable backorder for this product
            }
        )

        # Create a dummy partner to use in sale orders
        cls.partner = cls.ResPartner.create(
            {
                "name": "Dummy Partner",
            }
        )

    def test01_backorder_email(self):
        # Create a sale order with the product that allows backorders
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

        # Assert that backorder is allowed for the product
        self.assertTrue(self.product.allow_backorder)

        # Assert that the sale order is set to send backorder email notification
        self.assertTrue(sale_order.to_send_backorder_email)

        # Confirm the sale order, which should trigger processes related to the order
        sale_order.action_confirm()

        # Assert that after confirming the sale order, the flag to
        # send backorder email is cleared
        self.assertFalse(sale_order.to_send_backorder_email)
