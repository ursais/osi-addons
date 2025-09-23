from datetime import datetime,date, timedelta
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
        cls.ProductTemplate = cls.env["product.template"]
        cls.ProductProduct = cls.env["product.product"]
        cls.PriceReview = cls.env["product.price.review"]

        # Create a product template
        cls.product_template = cls.ProductTemplate.create(
            {
                "name": "Test Product",
                "config_ok": False,  # Standard product
            }
        )

        # Create a price review
        cls.price_review = cls.PriceReview.create(
            {
                "product_id": cls.product_template.product_variant_id.id,
            }
        )


    def _create_review(self, effective_date=None, state="new"):
        return self.env["product.price.review"].create(
            {
                "product_id": self.product_template.product_variant_id.id,
                "effective_date": effective_date,
                "state": state,
            }
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
        self.assertEqual(new_review1.approved_total_cost, 44.50)
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
        self.assertEqual(new_review1.product_id.approved_total_cost, 44.50)
        self.assertEqual(
            new_review1.product_id.last_purchase_margin, 0.5841121495327103
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
                            "date_planned": datetime.today()
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
        self.assertEqual(product_price_review01.product_id.approved_total_cost, 44.50)
        self.assertEqual(
            product_price_review01.product_id.last_purchase_margin, 1.4158878504672898
        )

    def test_action_view_price_reviews(self):
        """Test the action to view price reviews"""
        action = self.product_template.action_view_price_reviews()
        self.assertIn("domain", action)
        self.assertEqual(
            action["domain"],
            [("product_id", "in", self.product_template.product_variant_ids.ids)],
        )
        self.assertIn("context", action)
        self.assertFalse(action["context"].get("create"))  # Ensure creation is disabled

    def test_action_price_review(self):
        """Test action for opening a price review"""
        action = self.product_template.action_price_review()
        self.assertIsInstance(action, dict)  # Should return an action dictionary

    def test_compute_price_review(self):
        """Test computation of price_review_count"""
        self.product_template._compute_price_review()
        self.assertEqual(self.product_template.price_review_count, 1)

    def test_compute_can_create_price_review(self):
        """Test computation of can_create_price_review"""
        self.product_template._compute_can_create_price_review()
        self.assertTrue(
            self.product_template.can_create_price_review
        )  # Should be True since it's a standard product

    def test_validate_button_with_past_date(self):
        """Validation should raise an error if effective_date is before today."""
        review = self._create_review(effective_date=date.today() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            review.validate_button()

    def test_validate_button_with_future_date(self):
        """Validation should place the review into 'pending' if effective_date is in the future."""

        review = self._create_review(effective_date=date.today() + timedelta(days=3))
        review.validate_button()
        self.assertEqual(
            review.state, "pending", "Future dated review should not be validated"
        )

    def test_validate_button_with_today_date_sets_validate(self):
        """Validation should immediately validate the review if effective_date is today."""
        review = self._create_review(effective_date=date.today())
        review.validate_button()
        self.assertEqual(review.state, "validated")

    def test_validate_button_rejects_other_pending_reviews(self):
        """When a new pending review is created, existing pending reviews for the same"""
        """product are rejected and a chatter note is logged."""

        pending_review = self._create_review(
            effective_date=date.today() + timedelta(days=3), state="pending"
        )
        pending_review.validate_button()
        new_review = self._create_review(
            effective_date=date.today() + timedelta(days=3)
        )
        new_review.validate_button()
        self.assertEqual(new_review.state, "pending")
        self.assertEqual(pending_review.state, "reject")
        # chatter message check
        messages = pending_review.message_ids.mapped("body")
        self.assertTrue(
            any("Another price review was set to pending" in msg for msg in messages)
        )

    def test_reset_to_draft(self):
        """reset_to_draft should move a review from 'pending' back to 'draft' (new)."""
        review = self._create_review(effective_date=date.today(), state="pending")
        review.reset_to_draft()
        self.assertEqual(review.state, "new")

    def test_scheduled_action_process_pending_reviews(self):
        """The scheduled action should validate pending reviews whose effective_date is today or earlier."""
        review = self._create_review(effective_date=date.today(), state="pending")
        review._cron_process_pending_price_reviews()
        # should attempt to validate
        self.assertEqual(
            review.state,
            "validated",
            "Scheduled action should validate pending reviews",
        )
