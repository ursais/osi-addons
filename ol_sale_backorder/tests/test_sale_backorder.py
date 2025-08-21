# © 2025 Your Company - License OEEL-1
from odoo.tests import common
from odoo.fields import Command
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestNoBackorders(common.TransactionCase):
    """
    Unit tests for the no-backorder logic on sale.order.line.

    This suite covers:
    - Self-limited products (no backorders allowed)
    - Products allowing backorders (infinite availability)
    - Incoming stock logic
    - BoM-limited products via components that disallow backorders
    - Constraint enforcement when quantities exceed allowed caps
    """

    def setUp(self):
        super().setUp()

        # Create a partner to use in sale orders
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})

        # Get an existing warehouse (assumes stock module installed)
        self.warehouse = self.env["stock.warehouse"].search([], limit=1)
        self.stock_location = self.warehouse.lot_stock_id

        # Stockable product with no backorders allowed
        self.product_no_bo = self.env["product.product"].create(
            {
                "name": "No Backorder Product",
                "type": "product",
                "allow_backorder": False,
            }
        )

        # Stockable product with backorders allowed
        self.product_with_bo = self.env["product.product"].create(
            {
                "name": "With Backorder Product",
                "type": "product",
                "allow_backorder": True,
            }
        )

        # Give some free stock to the backorder-allowed product
        self.env["stock.quant"].create(
            {
                "product_id": self.product_with_bo.id,
                "location_id": self.stock_location.id,
                "quantity": 10,
            }
        )

    def test_max_sellable_qty_inf_for_backorder_product(self):
        """Products with allow_backorder=True should return infinite capacity."""
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
            }
        )
        sol = self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": self.product_with_bo.id,
                "product_uom_qty": 100,
            }
        )
        qty, sources = sol._max_sellable_qty_now()
        self.assertEqual(qty, float("inf"))
        self.assertEqual(sources, [])

    def test_max_sellable_qty_restricts_no_backorder_product(self):
        """No-backorder product capacity equals free available stock."""
        # Add 5 units of stock
        self.env["stock.quant"].create(
            {
                "product_id": self.product_no_bo.id,
                "location_id": self.stock_location.id,
                "quantity": 5,
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today(),
            }
        )
        sol = self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": self.product_no_bo.id,
                "product_uom_qty": 3,
            }
        )
        qty, sources = sol._max_sellable_qty_now()
        self.assertEqual(qty, 5)
        self.assertTrue(any(s[0] == self.product_no_bo for s in sources))

    def test_constraint_blocks_excess_qty(self):
        """Constraint should raise error if quantity exceeds allowed cap."""
        self.env["stock.quant"].create(
            {
                "product_id": self.product_no_bo.id,
                "location_id": self.stock_location.id,
                "quantity": 2,
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today(),
            }
        )

        with self.assertRaises(ValidationError):
            self.env["sale.order.line"].create(
                {
                    "order_id": so.id,
                    "product_id": self.product_no_bo.id,
                    "product_uom_qty": 5,  # Greater than available
                }
            )

    def test_incoming_stock_increases_cap(self):
        """Incoming confirmed moves before commitment date should increase cap."""
        self.env["stock.quant"].create(
            {
                "product_id": self.product_no_bo.id,
                "location_id": self.stock_location.id,
                "quantity": 0,
            }
        )

        # Create an incoming move for tomorrow
        self.env["stock.move"].create(
            {
                "product_id": self.product_no_bo.id,
                "product_uom_qty": 4,
                "product_uom": self.product_no_bo.uom_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.stock_location.id,
                "date": date.today() + timedelta(days=1),
                "state": "confirmed",
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today() + timedelta(days=2),
            }
        )
        sol = self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": self.product_no_bo.id,
                "product_uom_qty": 4,
            }
        )
        qty, _ = sol._max_sellable_qty_now()
        self.assertEqual(qty, 4)

    def test_bom_component_limits_qty(self):
        """Component with no backorder should limit finished product qty."""
        component = self.env["product.product"].create(
            {
                "name": "Component No BO",
                "type": "product",
                "allow_backorder": False,
            }
        )
        finished = self.env["product.product"].create(
            {
                "name": "Finished Product",
                "type": "product",
                "allow_backorder": True,
            }
        )

        # Only 2 units of the component in stock
        self.env["stock.quant"].create(
            {
                "product_id": component.id,
                "location_id": self.stock_location.id,
                "quantity": 2,
            }
        )

        # Create BoM: 1 unit of component per finished product
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": finished.product_tmpl_id.id,
                "product_uom_id": finished.uom_id.id,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": component.id,
                            "product_qty": 1.0,
                            "product_uom_id": component.uom_id.id,
                        }
                    )
                ],
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today(),
            }
        )
        sol = self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": finished.id,
                "product_uom_qty": 1,
                "bom_id": bom.id,
            }
        )

        qty, sources = sol._max_sellable_qty_now()
        self.assertEqual(qty, 2)  # Limited by component stock
        self.assertTrue(any(s[0] == component for s in sources))

    def test_bom_component_incoming_increases_cap(self):
        """Incoming stock for a component should increase BoM-limited qty."""
        component = self.env["product.product"].create(
            {
                "name": "Component Incoming",
                "type": "product",
                "allow_backorder": False,
            }
        )
        finished = self.env["product.product"].create(
            {
                "name": "Finished Incoming Product",
                "type": "product",
                "allow_backorder": True,
            }
        )

        # No current stock for component
        self.env["stock.quant"].create(
            {
                "product_id": component.id,
                "location_id": self.stock_location.id,
                "quantity": 0,
            }
        )

        # Incoming move of 3 units tomorrow
        self.env["stock.move"].create(
            {
                "product_id": component.id,
                "product_uom_qty": 3,
                "product_uom": component.uom_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.stock_location.id,
                "date": date.today() + timedelta(days=1),
                "state": "confirmed",
            }
        )

        # BoM: 1 component per finished product
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": finished.product_tmpl_id.id,
                "product_uom_id": finished.uom_id.id,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": component.id,
                            "product_qty": 1.0,
                            "product_uom_id": component.uom_id.id,
                        }
                    )
                ],
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today() + timedelta(days=2),
            }
        )
        sol = self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": finished.id,
                "product_uom_qty": 1,
                "bom_id": bom.id,
            }
        )

        qty, _ = sol._max_sellable_qty_now()
        self.assertEqual(qty, 3)  # Matches incoming qty

    def test_bom_constraint_blocks_excess_qty(self):
        """Constraint should block if BoM component limits are exceeded."""
        component = self.env["product.product"].create(
            {
                "name": "Component Limited",
                "type": "product",
                "allow_backorder": False,
            }
        )
        finished = self.env["product.product"].create(
            {
                "name": "Finished Limited Product",
                "type": "product",
                "allow_backorder": True,
            }
        )

        # Only 1 component in stock
        self.env["stock.quant"].create(
            {
                "product_id": component.id,
                "location_id": self.stock_location.id,
                "quantity": 1,
            }
        )

        # BoM: 1 component per finished product
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": finished.product_tmpl_id.id,
                "product_uom_id": finished.uom_id.id,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": component.id,
                            "product_qty": 1.0,
                            "product_uom_id": component.uom_id.id,
                        }
                    )
                ],
            }
        )

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "commitment_date": date.today(),
            }
        )

        # Attempt to sell more than available via component
        with self.assertRaises(ValidationError):
            self.env["sale.order.line"].create(
                {
                    "order_id": so.id,
                    "product_id": finished.id,
                    "product_uom_qty": 2,
                    "bom_id": bom.id,
                }
            )
