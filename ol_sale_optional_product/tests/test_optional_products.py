# Import Odoo libs
from odoo import fields
from odoo.tests import common, tagged
from odoo.exceptions import UserError
from datetime import date


@tagged("-at_install", "post_install")
class TestSaleOrderOption(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up basic test data: a sale order, product, and currency
        cls.currency_usd = cls.env["res.currency"].search(
            [("name", "=", "USD")], limit=1
        )
        cls.currency_eur = cls.env["res.currency"].search(
            [("name", "=", "EUR")], limit=1
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "standard_price": 100.0,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "cost_currency_id": cls.currency_usd.id,
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "currency_id": cls.currency_eur.id,
                "date_order": fields.Date.to_string(date.today()),
            }
        )
        cls.order_line = cls.env["sale.order.line"].create(
            {
                "order_id": cls.order.id,
                "product_id": cls.product.id,
                "product_uom_qty": 2,
                "price_unit": 200.0,
            }
        )

    def test_get_values_to_add_to_optional(self):
        """Test that the values dictionary is correctly created."""
        values = self.order_line._get_values_to_add_to_optional()
        self.assertEqual(values["order_id"], self.order.id)
        self.assertEqual(values["price_unit"], self.order_line.price_unit)
        self.assertEqual(values["product_id"], self.product.id)
        self.assertEqual(values["quantity"], self.order_line.product_uom_qty)

    def test_button_add_to_optional(self):
        """Test that the button calls the appropriate method without error."""
        self.order_line.button_add_to_optional()
        option_lines = self.env["sale.order.option"].search(
            [("order_id", "=", self.order.id)]
        )
        self.assertTrue(option_lines, "Option line should be created by button action.")
        self.assertEqual(option_lines[0].product_id, self.product)

    def test_add_option_to_optional(self):
        """Test that options can be added to editable orders and raise an
        error on confirmed orders."""
        self.order.state = "draft"  # Ensure the order is editable
        option_line = self.order_line.add_option_to_optional()
        self.assertEqual(option_line.order_id, self.order)
        self.assertEqual(option_line.product_id, self.product)

        # Confirm the order to make it non-editable
        self.order.state = "sale"
        with self.assertRaises(UserError):
            self.order_line.add_option_to_optional()

    def test_convert_to_sol_currency(self):
        """Test currency conversion to sale order line currency."""
        # Example amount in USD, order currency in EUR
        amount_usd = 100
        converted_amount = self.order_line._convert_to_sol_currency(
            amount_usd, self.currency_usd
        )
        self.assertNotEqual(
            converted_amount,
            amount_usd,
            "Amount should be converted to order currency.",
        )

        # When currencies match, the amount should be unchanged
        amount_same_currency = self.order_line._convert_to_sol_currency(
            amount_usd, self.currency_eur
        )
        self.assertEqual(
            amount_same_currency,
            amount_usd,
            "Amount should be unchanged if currencies are the same.",
        )

    def test_compute_purchase_price(self):
        """Test that purchase price is computed and converted correctly."""
        self.order_line._compute_purchase_price()
        expected_purchase_price = self.order_line._convert_to_sol_currency(
            self.product.standard_price, self.product.cost_currency_id
        )
        self.assertEqual(self.order_line.purchase_price, expected_purchase_price)

    def test_compute_margin(self):
        """Test margin and margin percentage calculation."""
        self.order_line.purchase_price = 80.0
        self.order_line.price_subtotal = (
            self.order_line.price_unit * self.order_line.product_uom_qty
        )
        self.order_line._compute_margin()

        expected_margin = self.order_line.price_subtotal - (
            self.order_line.purchase_price * self.order_line.product_uom_qty
        )
        expected_margin_percent = (
            (expected_margin / self.order_line.price_subtotal)
            if self.order_line.price_subtotal
            else 0
        )

        self.assertAlmostEqual(self.order_line.margin, expected_margin)
        self.assertAlmostEqual(self.order_line.margin_percent, expected_margin_percent)

    def test_compute_amount(self):
        """Test that the price_subtotal is calculated correctly with and
        without discount."""
        # Test with discount
        self.order_line.discount = 10  # 10%
        self.order_line._compute_amount()
        expected_subtotal_discounted = (
            self.order_line.price_unit * self.order_line.product_uom_qty
        ) * 0.9
        self.assertAlmostEqual(
            self.order_line.price_subtotal, expected_subtotal_discounted
        )

        # Test without discount
        self.order_line.discount = 0
        self.order_line._compute_amount()
        expected_subtotal = self.order_line.price_unit * self.order_line.product_uom_qty
        self.assertEqual(self.order_line.price_subtotal, expected_subtotal)
