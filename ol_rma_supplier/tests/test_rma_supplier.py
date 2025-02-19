from odoo.tests import common, tagged

from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


@tagged("-at_install", "post_install")
class TestStockWarehouse(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Company Reference
        cls.company = cls.env.company.id

        # Create a warehouse
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Test Warehouse", "company_id": cls.company, "code": "RMA Test"}
        )

    def test_write_rma_in_this_wh_true(self):
        """Test when 'rma_in_this_wh' is set to True"""
        # Set rma_in_this_wh to True
        self.warehouse.write({"rma_in_this_wh": True})

        # Check if the RMA location is created
        self.assertTrue(self.warehouse.lot_rma_id, "RMA Location should be created")
        self.assertEqual(
            self.warehouse.lot_rma_id.name,
            "RMA",
            "RMA Location should have correct name",
        )

        # Check if the RMA picking types are created
        self.assertTrue(
            self.warehouse.rma_sup_out_type_id,
            "RMA Supplier Out Picking Type should be created",
        )
        self.assertTrue(
            self.warehouse.rma_sup_in_type_id,
            "RMA Supplier In Picking Type should be created",
        )

        # Check if the RMA rules are created
        self.assertTrue(
            self.warehouse.rma_supplier_in_pull_id,
            "RMA Supplier In Pull Rule should be created",
        )
        self.assertTrue(
            self.warehouse.rma_supplier_out_pull_id,
            "RMA Supplier Out Pull Rule should be created",
        )

    def test_write_rma_in_this_wh_false(self):
        """Test when 'rma_in_this_wh' is set to False"""
        # Set rma_in_this_wh to True first to simulate the creation of RMA settings
        self.warehouse.write({"rma_in_this_wh": True})

        # Now set rma_in_this_wh to False and check the deactivation of RMA related settings
        self.warehouse.write({"rma_in_this_wh": False})

        # Check if the RMA location is not deleted but should be inactive
        self.assertFalse(
            self.warehouse.rma_sup_out_type_id.active,
            "RMA Supplier Out Picking Type should be inactive",
        )
        self.assertFalse(
            self.warehouse.rma_sup_in_type_id.active,
            "RMA Supplier In Picking Type should be inactive",
        )

        # Check if the RMA rules are unlinked (deleted)
        self.assertFalse(
            self.warehouse.rma_supplier_in_pull_id,
            "RMA Supplier In Pull Rule should be deleted",
        )
        self.assertFalse(
            self.warehouse.rma_supplier_out_pull_id,
            "RMA Supplier Out Pull Rule should be deleted",
        )

    def test_write_without_rma_in_this_wh(self):
        """Test when 'rma_in_this_wh' is not set and check if RMA settings are untouched"""
        initial_rma_out_type = self.warehouse.rma_sup_out_type_id
        initial_rma_in_type = self.warehouse.rma_sup_in_type_id

        # Ensure the warehouse doesn't have RMA settings initially
        self.assertFalse(initial_rma_out_type)
        self.assertFalse(initial_rma_in_type)

        # Write without setting 'rma_in_this_wh'
        self.warehouse.write({"name": "Updated Warehouse"})

        # Check if RMA settings are still untouched
        self.assertFalse(
            self.warehouse.rma_sup_out_type_id,
            "RMA Supplier Out Picking Type should not be created",
        )
        self.assertFalse(
            self.warehouse.rma_sup_in_type_id,
            "RMA Supplier In Picking Type should not be created",
        )

    def test_write_rma_in_this_wh_and_existing_rma(self):
        """Test 'rma_in_this_wh' as True when RMA settings already exist"""
        # Set up initial RMA settings manually
        self.warehouse.write({"rma_in_this_wh": True})

        # Now set 'rma_in_this_wh' again to True and check if settings are not recreated
        self.warehouse.write({"rma_in_this_wh": True})

        # The RMA location and types should already exist, so they should not be recreated
        self.assertEqual(
            self.warehouse.lot_rma_id.name, "RMA", "RMA Location should already exist"
        )
        self.assertTrue(
            self.warehouse.rma_sup_out_type_id,
            "RMA Supplier Out Picking Type should exist",
        )
        self.assertTrue(
            self.warehouse.rma_sup_in_type_id,
            "RMA Supplier In Picking Type should exist",
        )


@tagged("-at_install", "post_install")
class TestRmaSupplierLine(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Company Reference
        cls.company = cls.env.company.id
        # Create the necessary records for the test
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.partner_id = cls.env["res.partner"].create({"name": "Test Partner"}).id
        cls.uom = cls.env.ref("uom.product_uom_categ_unit").id
        cls.out_warehouse_id = cls.env.ref("stock.warehouse0")
        cls.out_operation_id = cls.out_warehouse_id.rma_sup_out_type_id.id
        cls.out_location_id = cls.out_warehouse_id.lot_rma_id.id
        cls.in_warehouse_id = cls.env.ref("stock.warehouse0")
        cls.in_operation_id = cls.in_warehouse_id.rma_sup_in_type_id.id
        cls.in_location_id = cls.in_warehouse_id.lot_rma_id.id

        cls.rma_order = cls.env["rma.supplier.order"].create(
            {
                "name": "RMA Order 001",
                "company_id": cls.company,
                "partner_id": cls.partner_id,
                "out_warehouse_id": cls.out_warehouse_id.id,
                "out_operation_id": cls.out_operation_id,
                "out_location_id": cls.out_location_id,
                "in_operation_id": cls.in_operation_id,
                "in_location_id": cls.in_location_id,
            }
        )

        cls.rma_line = cls.env["rma.supplier.order.line"].create(
            {
                "rma_order_id": cls.rma_order.id,
                "product_id": cls.product.id,
                "quantity": 5.0,
                "product_uom": cls.uom,
            }
        )

    def test_name_computation(self):
        """Test the computed 'name' field."""
        # Check the initial value of the name field
        self.assertEqual(
            self.rma_line.name,
            "RMA Order 001 - Test Product",
            "The name field is not computed correctly.",
        )

        # Update the name field directly
        self.rma_line.write({"name": "Updated Name"})

        # Recompute the name (the field should now reflect the updated name format)
        self.rma_line._compute_name()
        self.assertEqual(
            self.rma_line.name,
            "RMA Order 001 - Updated Name",
            "The name field should reflect the updated name.",
        )

    def test_product_uom_computation(self):
        """Test that the product's unit of measure is computed correctly."""
        # Initially, the UOM should be the same as the product's default UOM
        self.assertEqual(
            self.rma_line.product_uom,
            self.product.uom_id,
            "The UOM should match the product's default UOM.",
        )

        # Change the UOM
        new_uom = self.env["uom.uom"].create(
            {
                "name": "New UOM",
                "category_id": self.env.ref("uom.product_uom_categ_unit").id,
                "uom_type": "bigger",
                "ratio": 10,
            }
        )
        self.rma_line.write({"product_uom": new_uom.id})

        # Ensure that the UOM is updated
        self.assertEqual(
            self.rma_line.product_uom, new_uom, "The UOM should be updated."
        )

        # Ensure that the UOM field is properly recomputed when product is changed
        self.rma_line.product_id = self.product
        self.assertEqual(
            self.rma_line.product_uom,
            self.product.uom_id,
            "The UOM should be reset to the product's default UOM.",
        )

    def test_qty_delivered_and_qty_received(self):
        """Test the computation of delivered and received quantities."""
        # Create some stock moves for the RMA line (outgoing and incoming)
        stock_location = self.env.ref("stock.stock_location_stock")
        supplier_location = self.env.ref("stock.stock_location_suppliers")

        # Create stock moves for outgoing and incoming quantities
        move_out = self.env["stock.move"].create(
            {
                "name": "Outgoing Move",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 5.0,
                "location_id": stock_location.id,
                "location_dest_id": supplier_location.id,
                "state": "done",
                "rma_supplier_line_id": self.rma_line.id,
            }
        )

        move_in = self.env["stock.move"].create(
            {
                "name": "Incoming Move",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 3.0,
                "location_id": supplier_location.id,
                "location_dest_id": stock_location.id,
                "state": "done",
                "rma_supplier_line_id": self.rma_line.id,
            }
        )

        # Computed quantities
        self.rma_line._compute_qty_delivered_received()

        # Assertions
        self.assertEqual(
            self.rma_line.qty_delivered, 5.0, "Delivered quantity should be 5.0"
        )
        self.assertEqual(
            self.rma_line.qty_received, 3.0, "Received quantity should be 3.0"
        )

    def test_qty_delivered_and_qty_received_no_moves(self):
        """Test that delivered and received quantities are 0 when there are no moves."""
        # Ensure that qty_delivered and qty_received are 0 when there are no stock moves
        self.rma_line._compute_qty_delivered_received()

        self.assertEqual(
            self.rma_line.qty_delivered,
            0.0,
            "The delivered quantity should be 0 when there are no moves.",
        )
        self.assertEqual(
            self.rma_line.qty_received,
            0.0,
            "The received quantity should be 0 when there are no moves.",
        )


@tagged("-at_install", "post_install")
class TestRmaSupplier(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company.id
        cls.warehouse = cls.env.ref("stock.warehouse0")
        # Create necessary records
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "company_id": cls.company,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.out_operation_id = cls.warehouse.rma_sup_out_type_id.id
        cls.out_location_id = cls.warehouse.lot_rma_id.id
        cls.in_operation_id = cls.warehouse.rma_sup_in_type_id.id
        cls.in_location_id = cls.warehouse.lot_rma_id.id

        # Create the RMA Supplier order
        cls.rma_order = cls.env["rma.supplier.order"].create(
            {
                "partner_id": cls.partner.id,
                "in_warehouse_id": cls.warehouse.id,
                "out_warehouse_id": cls.warehouse.id,
                "out_operation_id": cls.out_operation_id,
                "out_location_id": cls.out_location_id,
                "in_operation_id": cls.in_operation_id,
                "in_location_id": cls.in_location_id,
            }
        )

        # Add a line to the RMA order
        cls.rma_line = cls.env["rma.supplier.order.line"].create(
            {
                "rma_order_id": cls.rma_order.id,
                "product_id": cls.product.id,
                "quantity": 2.0,
            }
        )

    def test_create_rma_supplier(self):
        """Test the creation of an RMA Supplier order."""
        self.assertNotEqual(
            self.rma_order.name, "New", "The RMA order name should be 'New'."
        )
        self.assertEqual(
            self.rma_order.state, "draft", "The RMA order state should be 'draft'."
        )
        self.assertEqual(
            len(self.rma_order.line_ids),
            1,
            "There should be one RMA line in the order.",
        )

    def test_rma_confirm(self):
        """Test confirming an RMA and creating stock pickings."""
        self.rma_order.action_confirm()

        self.assertEqual(
            self.rma_order.state, "confirm", "The RMA order state should be 'confirm'."
        )
        self.assertGreater(
            len(self.rma_order.out_transfer_ids),
            0,
            "There should be outbound transfers created.",
        )
        self.assertGreater(
            len(self.rma_order.in_transfer_ids),
            0,
            "There should be inbound transfers created.",
        )

    def test_rma_confirm_without_products(self):
        """Test confirming an RMA without adding products."""
        # Create an RMA order with no products
        rma_order_without_lines = self.env["rma.supplier.order"].create(
            {
                "partner_id": self.partner.id,
                "in_warehouse_id": self.warehouse.id,
                "out_warehouse_id": self.warehouse.id,
                "out_operation_id": self.out_operation_id,
                "out_location_id": self.out_location_id,
                "in_operation_id": self.in_operation_id,
                "in_location_id": self.in_location_id,
            }
        )

        with self.assertRaises(UserError):
            rma_order_without_lines.action_confirm()

    def test_rma_cancel(self):
        """Test canceling an RMA order and canceling related transfers."""
        self.rma_order.action_confirm()
        self.rma_order.action_cancel()

        self.assertEqual(
            self.rma_order.state, "cancel", "The RMA order state should be 'cancel'."
        )
        self.assertEqual(
            len(
                self.rma_order.out_transfer_ids.filtered(lambda t: t.state != "cancel")
            ),
            0,
            "There should be no non-canceled out transfers.",
        )
        self.assertEqual(
            len(self.rma_order.in_transfer_ids.filtered(lambda t: t.state != "cancel")),
            0,
            "There should be no non-canceled in transfers.",
        )

    def test_rma_reset_to_draft(self):
        """Test resetting an RMA order to draft state."""
        self.rma_order.action_confirm()
        self.rma_order.action_reset_to_draft()

        self.assertEqual(
            self.rma_order.state,
            "draft",
            "The RMA order state should be 'draft' after reset.",
        )

    def test_receipt_and_deliver_status(self):
        """Test the computation of receipt and delivery status based on stock pickings."""
        # Create stock pickings and change their states
        self.rma_order.action_confirm()

        # Simulate the "done" state for both inbound and outbound transfers
        for picking in self.rma_order.out_transfer_ids:
            picking.button_validate()

        for picking in self.rma_order.in_transfer_ids:
            picking.button_validate()

        # Recompute the statuses
        self.rma_order._compute_receipt_deliver_status()

        self.assertEqual(
            self.rma_order.deliver_status,
            "full",
            "The deliver status should be 'full'.",
        )
        self.assertEqual(
            self.rma_order.receipt_status,
            "full",
            "The receipt status should be 'full'.",
        )

    def test_onchange_in_warehouse_id(self):
        """Test the onchange behavior for in_warehouse_id field."""
        warehouse2 = self.env["stock.warehouse"].create(
            {"name": "Warehouse 2", "company_id": self.company, "code": "Odoo"}
        )
        self.rma_order.write({"in_warehouse_id": warehouse2.id})
        self.rma_order._onchange_in_warehouse_id()

        self.assertEqual(
            self.rma_order.in_operation_id,
            warehouse2.rma_sup_in_type_id,
            "The in_operation_id should be updated correctly.",
        )
        self.assertEqual(
            self.rma_order.in_location_id,
            warehouse2.lot_rma_id,
            "The in_location_id should be updated correctly.",
        )

    def test_onchange_out_warehouse_id(self):
        """Test the onchange behavior for out_warehouse_id field."""
        warehouse2 = self.env["stock.warehouse"].create(
            {"name": "Warehouse 2", "company_id": self.company, "code": "Test v1"}
        )
        self.rma_order.write({"out_warehouse_id": warehouse2.id})
        self.rma_order._onchange_out_warehouse_id()

        self.assertEqual(
            self.rma_order.out_operation_id,
            warehouse2.rma_sup_out_type_id,
            "The out_operation_id should be updated correctly.",
        )
        self.assertEqual(
            self.rma_order.out_location_id,
            warehouse2.lot_rma_id,
            "The out_location_id should be updated correctly.",
        )


@tagged("-at_install", "post_install")
class TestResPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create necessary records
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "company_id": cls.company.id,
                "code": "RMATEST",
            }
        )
        cls.warehouse.write({"rma_in_this_wh": True})

        cls.out_operation_id = cls.warehouse.rma_sup_out_type_id.id
        cls.out_location_id = cls.warehouse.lot_rma_id.id
        cls.in_operation_id = cls.warehouse.rma_sup_in_type_id.id
        cls.in_location_id = cls.warehouse.lot_rma_id.id

        # Create RMA Supplier Orders and link them to the partner
        cls.rma_order_1 = cls.env["rma.supplier.order"].create(
            {
                "partner_id": cls.partner.id,
                "in_warehouse_id": cls.warehouse.id,
                "out_warehouse_id": cls.warehouse.id,
                "out_operation_id": cls.out_operation_id,
                "out_location_id": cls.out_location_id,
                "in_operation_id": cls.in_operation_id,
                "in_location_id": cls.in_location_id,
            }
        )
        cls.rma_order_2 = cls.env["rma.supplier.order"].create(
            {
                "partner_id": cls.partner.id,
                "in_warehouse_id": cls.warehouse.id,
                "out_warehouse_id": cls.warehouse.id,
                "out_operation_id": cls.out_operation_id,
                "out_location_id": cls.out_location_id,
                "in_operation_id": cls.in_operation_id,
                "in_location_id": cls.in_location_id,
            }
        )

    def test_rma_supplier_order_count(self):
        """Test the computation of the RMA supplier order count."""
        self.partner._compute_rma_supplier_order_count()
        self.assertEqual(
            self.partner.rma_supplier_order_count,
            2,
            "The partner should have 2 RMA orders.",
        )

    def test_action_view_rma_supplier_orders(self):
        """Test the action to view the supplier RMA orders."""
        action = self.partner.action_view_rma_supplier_orders()

        # Test case where there is more than one RMA order, it should open the tree view
        self.assertIn("views", action, "The action should contain 'views'.")
        self.assertEqual(
            action["views"][0][1], "tree", "The first view should be the tree view."
        )
        self.assertIn("domain", action, "The action should contain 'domain'.")
        self.assertEqual(
            action["domain"],
            [("id", "in", [self.rma_order_1.id, self.rma_order_2.id])],
            "The domain should include both RMA orders.",
        )

    def test_action_view_single_rma_supplier_order(self):
        """Test the action to view a single supplier RMA order."""
        # For this, we simulate that there's only one RMA order
        self.rma_order_2.unlink()
        action = self.partner.action_view_rma_supplier_orders()

        # Test case where there is exactly one RMA order, it should open the form view
        self.assertIn("views", action, "The action should contain 'views'.")
        self.assertEqual(
            action["views"][0][1], "form", "The first view should be the form view."
        )
        self.assertEqual(
            action["res_id"], self.rma_order_1.id, "The RMA order ID should match."
        )
