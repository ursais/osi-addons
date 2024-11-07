# Import Odoo libs
from odoo.tests import common, tagged
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestMrpProductionBatch(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        # Set up initial data for sale order to batch testing
        # Creating a mock product with serial tracking and split allowed
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "tracking": "serial",
                "is_allow_split_mo": True,
            }
        )

        # Create a manufacturing order for the product
        cls.mo = cls.env["mrp.production"].create(
            {
                "product_id": cls.product.id,
                "product_qty": 2,
            }
        )

        # Create a sale order with the manufacturing order attached
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "mrp_production_ids": [(6, 0, [cls.mo.id])],
            }
        )

        # Set up initial data for batch testing
        cls.user = cls.env.user
        cls.batch = cls.env["mrp.production.batch"].create(
            {
                "name": "Test Batch",
                "responsible_id": cls.user.id,
                "state": "draft",
            }
        )
        cls.production_order = cls.env["mrp.production"].create(
            {
                "name": "Test Production",
                "product_id": cls.env.ref("product.product_product_1").id,
                "product_qty": 10.0,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "mrp_batch_id": cls.batch.id,
            }
        )

    # TEST SALE ORDER FUNCTIONALITY
    def test_sale_order_action_confirm(self):
        # Confirm the sale order
        self.sale_order.action_confirm()

        # Assert the sale order is confirmed
        self.assertEqual(
            self.sale_order.state, "sale", "The sale order should be confirmed."
        )

        # Check that split_mo has been triggered by confirming there is a new batch
        self.sale_order.split_mo()  # We call it here for synchronous behavior in testing
        self.assertTrue(
            self.sale_order.mrp_production_ids.mrp_batch_id,
            "A batch should be created for the MO.",
        )

    def test_split_mo(self):
        # Run split_mo directly to test the splitting functionality
        self.sale_order.split_mo()

        # Check if the manufacturing order was split into quantities of 1
        split_orders = self.env["mrp.production"].search(
            [("product_id", "=", self.product.id)]
        )
        self.assertEqual(
            len(split_orders),
            2,
            "There should be 2 manufacturing orders after the split.",
        )

    def test_compute_mrp_production_batch_id_count(self):
        # Manually call the compute method
        self.sale_order._compute_mrp_production_batch_id_count()

        # Check if the batch count is as expected
        self.assertEqual(
            self.sale_order.mrp_batch_count,
            1,
            "Batch count should be 1 after creation.",
        )

    def test_action_view_mrp_production_batch_single_batch(self):
        # Confirm the sale order to trigger batch creation
        self.sale_order.action_confirm()

        # Run action_view_mrp_production_batch on a single batch
        action = self.sale_order.action_view_mrp_production_batch()

        # Check if the view opens in form mode
        self.assertEqual(
            action["view_mode"], "form", "Should open in form view for a single batch."
        )
        self.assertEqual(
            action["res_id"],
            self.sale_order.mrp_production_ids.mrp_batch_id.id,
            "Form view should show the correct batch.",
        )

    def test_action_view_mrp_production_batch_multiple_batches(self):
        # Add a second manufacturing order with a different batch to simulate multiple batches
        mo2 = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "product_qty": 1,
            }
        )
        self.sale_order.mrp_production_ids = [(4, mo2.id)]

        # Run the action to view the batches
        action = self.sale_order.action_view_mrp_production_batch()

        # Check if the view opens in tree and form mode with the correct domain
        self.assertEqual(
            action["view_mode"],
            "tree,form",
            "Should open in tree,form view for multiple batches.",
        )
        self.assertIn(
            "domain", action, "Action should have a domain to filter the batches."
        )
        self.assertIn(
            ("id", "in", self.sale_order.mrp_production_ids.mrp_batch_id.ids),
            action["domain"],
            "The domain should filter for all batch IDs related to the sale order.",
        )

    # TEST BATCH FUNCTIONS
    def test_action_assign(self):
        """Test that action_assign reserves raw materials and sets is_queuing."""
        self.batch.action_assign()
        self.assertTrue(self.batch.is_queuing)
        # Ensure all production orders are assigned
        for production in self.batch.production_ids:
            self.assertEqual(production.state, "assigned")

    def test_action_confirm(self):
        """Test action_confirm sets the batch state to confirm and confirms orders."""
        self.batch.action_confirm()
        self.assertEqual(self.batch.state, "confirm")
        # Verify each production is confirmed
        for production in self.batch.production_ids:
            self.assertIn(production.state, ("confirmed", "progress"))

    def test_button_plan(self):
        """Test button_plan sets the batch state to confirm and plans orders."""
        self.batch.button_plan()
        self.assertEqual(self.batch.state, "confirm")
        # Verify each production is planned
        for production in self.batch.production_ids:
            self.assertEqual(production.state, "planned")

    def test_button_unplan(self):
        """Test button_unplan sets productions to unplanned state."""
        self.batch.button_plan()
        self.batch.button_unplan()
        for production in self.batch.production_ids:
            self.assertEqual(production.state, "draft")

    def test_action_done(self):
        """Test action_done sets batch to done and completes production orders."""
        self.batch.action_done()
        self.assertEqual(self.batch.state, "done")
        # Verify productions are done
        for production in self.batch.production_ids:
            self.assertEqual(production.state, "done")

    def test_action_cancel(self):
        """Test action_cancel sets batch and production orders to cancel."""
        self.batch.action_cancel()
        self.assertEqual(self.batch.state, "cancel")
        for production in self.batch.production_ids:
            self.assertEqual(production.state, "cancel")

    def test_compute_total_duration(self):
        """Test total_duration computed field."""
        self.production_order.duration = 5.0
        self.batch._compute_total_duration()
        self.assertEqual(self.batch.total_duration, 5.0)

    def test_compute_total_duration_expected(self):
        """Test total_duration_expected computed field."""
        self.production_order.duration_expected = 10.0
        self.batch._compute_total_duration_expected()
        self.assertEqual(self.batch.total_duration_expected, 10.0)

    def test_compute_sale_order_count(self):
        """Test sale_order_count computes correctly based on production orders."""
        self.batch._compute_sale_order_count()
        self.assertEqual(self.batch.sale_order_count, len(self.batch.production_ids))

    def test_action_view_sale(self):
        """Test action_view_sale returns the correct sale order action."""
        action = self.batch.action_view_sale()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(action["view_mode"], "tree,form")
        self.assertIn("domain", action)
