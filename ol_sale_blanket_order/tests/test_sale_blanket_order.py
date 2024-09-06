from datetime import date, timedelta

from odoo import fields
from odoo.tests import common


class TestSaleBlanketOrder(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        # Set up the test environment, create necessary objects and data for testing
        super().setUpClass()
        cls.blanket_order_obj = cls.env["sale.blanket.order"]
        cls.so_obj = cls.env["sale.order"]

        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )

        # Create a custom unit of measure (UoM) for testing
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")
        cls.uom_dozen = cls.env["uom.uom"].create(
            {
                "name": "Test-DozenA",
                "category_id": cls.categ_unit.id,
                "factor_inv": 12,
                "uom_type": "bigger",
                "rounding": 0.001,
            }
        )

        # Create a test customer (partner)
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "TEST CUSTOMER",
                "property_product_pricelist": cls.sale_pricelist.id,
            }
        )

        # Create a test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Demo",
                "categ_id": cls.env.ref("product.product_category_1").id,
                "standard_price": 35.0,
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL01",
                "sale_delay": 0,
            }
        )

        # Calculate tomorrow's date
        cls.tomorrow = date.today() + timedelta(days=1)

    def test_01_create_blanket_order_with_so(self):
        """Test creating a blanket order with associated sale orders."""
        # Create a blanket order with one line item
        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.partner.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 20.0,
                            "price_unit": 30.0,
                            "date_schedule": fields.Date.today(),
                        },
                    ),
                ],
            }
        )

        # Trigger onchange for partner to update related fields
        blanket_order.sudo().onchange_partner_id()

        # Confirm the blanket order
        blanket_order.sudo().action_confirm()

        # Check that the blanket order has one line item
        self.assertEqual(len(blanket_order.line_ids), 1)

        # Run the cron job to create sale orders from the blanket order
        self.blanket_order_obj.create_sale_order_cron()

        # Check that the blanket order is in the 'done' state
        self.assertEqual(blanket_order.state, "done")

        # View the sale orders created from the blanket order
        view_action = blanket_order.action_view_sale_orders()
        domain_ids = view_action["domain"][0][2]

        # Check that one sale order was created
        self.assertEqual(len(domain_ids), 1)

        # Browse the created sale order
        sale_order = self.so_obj.browse(domain_ids)

        # Check that the origin of the sale order matches the blanket order name
        self.assertEqual(sale_order.origin, blanket_order.name)

        # Get the sale order IDs linked to the blanket order lines
        so = blanket_order.mapped("line_ids.sale_lines.order_id.id")

        # Check that the created sale order ID is in the list
        self.assertIn(sale_order.id, so)

    def test_02_create_blanket_order_without_so(self):
        """Test creating a blanket order without generating sale orders."""
        # Set the sale delay to 2 days
        self.product.sale_delay = 2

        # Create a blanket order with one line item
        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.partner.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 20.0,
                            "price_unit": 30.0,
                            "date_schedule": fields.Date.today(),
                        },
                    ),
                ],
            }
        )

        # Trigger onchange for partner to update related fields
        blanket_order.onchange_partner_id()

        # Confirm the blanket order
        blanket_order.action_confirm()

        # Run the cron job to create sale orders from the blanket order
        self.blanket_order_obj.create_sale_order_cron()

        # Check that the blanket order is not in the 'done' state
        self.assertNotEqual(blanket_order.state, "done")

        # Get the sale order IDs linked to the blanket order lines
        so = blanket_order.mapped("line_ids.sale_lines.order_id.id")

        # Check that no sale orders were created
        self.assertFalse(so)
