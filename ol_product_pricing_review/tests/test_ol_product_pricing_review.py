from odoo.tests import common, tagged
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestOlProductPriceReview(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the test class by initializing the environment, companies, product categories,
        partner, and delivery carrier multiplier.
        """
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.company1 = cls.env.ref("ol_base.onlogic_eu")
        cls.company2 = cls.env.ref("base.main_company")

        cls.product_catg = cls.env.ref("product.product_category_all")

        cls.partner_id = cls.env["res.partner"].create({"name": "Vandan Pandeji"})

        cls.delivery_carrier_multiplier = cls.env["delivery.carrier.multiplier"].create(
            {"carrier": "Test carrier", "multiplier": 25}
        )

    def test_price_review_01(self):
        """
        Test the product price review process including creating a product,
        performing a price review based on override price and special price,
        and validating the review. Also tests the purchase order creation and
        rejection process.
        """
        # Create a product template for testing
        test_product_tmpl2 = self.env["product.template"].create(
            {
                "name": "Price Review Product - 2",
                "type": "product",
                "categ_id": self.product_catg.id,
                "standard_price": 50.00,
                "list_price": 100.00,
                "carrier_multiplier_id": self.delivery_carrier_multiplier.id,
                "weight": 1.5,
                "company_id": self.company2.id,
                "default_code": "PPR",
                "margin_min": 5.0,
                "margin_max": 6.0,
            }
        )
        # Search for a new product price review and trigger onchange
        new_review1 = self.env["product.price.review"].search(
            [
                ("product_id", "=", test_product_tmpl2.product_variant_id.id),
                ("company_id", "=", self.company2.id),
                ("state", "=", "new"),
            ]
        )
        # Update review based on override price and verify calculations
        new_review1.onchange_product_id()

        # Update review based on override price and verify calculations
        new_review1.write(
            {
                "tariff_percent": 1,
                "tooling_cost": 2,
                "override_margin": 5.0,
                "defrayment_cost": 5,
                "override_price": 102.0,
                "charm_price": ".00",
            }
        )
        self.assertEqual(new_review1.calculated_price, 44.5)
        self.assertEqual(new_review1.final_price, 102.0)
        self.assertEqual(new_review1.total_cost, 44.50)
        self.assertEqual(new_review1.margin, 57.50)
        self.assertEqual(new_review1.margin_percent, 0.5637254901960784)
        self.assertEqual(new_review1.origin_default_shipping_cost, 37.5)
        self.assertEqual(new_review1.origin_last_purchase_margin, 1.375)

        # Update review based on special price and verify calculations
        new_review1.write({"special_price": 107.0})
        self.assertEqual(new_review1.final_price, 107.0)
        self.assertEqual(new_review1.margin, 62.50)
        self.assertEqual(new_review1.margin_percent, 0.5841121495327103)

        # Assign and validate the review
        new_review1.assign_to_me()
        new_review1.validate_button()

        # Verify product fields updated after review validation
        self.assertEqual(new_review1.product_id.tariff_percent, 1.0)
        self.assertEqual(new_review1.product_id.tooling_cost, 2.0)
        self.assertEqual(new_review1.product_id.defrayment_cost, 5.0)
        self.assertEqual(new_review1.product_id.override_price, 102.0)
        self.assertEqual(new_review1.product_id.special_price, 107.0)
        self.assertEqual(new_review1.product_id.total_cost, 44.50)
        self.assertEqual(
            new_review1.product_id.last_purchase_margin, 1.4158878504672898
        )

        # Create a purchase order and confirm it
        PurchaseOrder = self.env["purchase.order"]
        test_purchase_order = PurchaseOrder.create(
            {
                "partner_id": self.partner_id.id,
                "company_id": self.company2.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": test_product_tmpl2.product_variant_id.id,
                            "product_qty": 10,
                            "price_unit": 53.50,
                        },
                    )
                ],
            }
        )
        test_purchase_order.button_confirm()

        # Search for a new product price review and reject it
        new_review2 = self.env["product.price.review"].search(
            [
                ("product_id", "=", test_product_tmpl2.product_variant_id.id),
                ("company_id", "=", self.company2.id),
                ("state", "=", "new"),
            ]
        )
        new_review2.reject_button()

        # Update the product template with new margin thresholds and validate
        test_product_tmpl2.write(
            {"enable_margin_threshold": True, "margin_min": 90.0, "margin_max": 92.0}
        )

        # Create and validate a new price review
        PriceReview = self.env["product.price.review"]
        product_price_review01 = PriceReview.create(
            {
                "product_id": test_product_tmpl2.product_variant_id.id,
            }
        )
        product_price_review01.onchange_product_id()

        # Assert that the review is in the correct initial state
        self.assertEqual(product_price_review01.state, "new")
        self.assertEqual(
            product_price_review01.product_id.id,
            test_product_tmpl2.product_variant_id.id,
        )

        # Validate the price review
        product_price_review01.validate_button()

        # Assert that the review has been validated
        self.assertEqual(product_price_review01.state, "validated")

        # Verify product fields updated after review validation
        self.assertEqual(product_price_review01.product_id.tariff_percent, 1.0)
        self.assertEqual(product_price_review01.product_id.tooling_cost, 2.0)
        self.assertEqual(product_price_review01.product_id.defrayment_cost, 5.0)
        self.assertEqual(product_price_review01.product_id.override_price, 102.0)
        self.assertEqual(product_price_review01.product_id.special_price, 107.0)
        self.assertEqual(product_price_review01.product_id.total_cost, 44.50)
        self.assertEqual(
            product_price_review01.product_id.last_purchase_margin, 1.4158878504672898
        )
