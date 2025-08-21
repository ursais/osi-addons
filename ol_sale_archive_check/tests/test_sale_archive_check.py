from odoo.tests import common
from odoo.fields import Command


class TestSaleOrderArchive(common.TransactionCase):
    """
    Functional tests for archive-check behavior on sale orders and order lines.
    These tests verify that when a product or its BOM is archived:
      - The sale order and lines are flagged appropriately
      - The chatter logs are updated when copying orders
    """

    def setUp(self):
        super(TestSaleOrderArchive, self).setUp()

        # Create a partner for the sale order
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Create an active product (will be linked to a BOM)
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "active": True,
            }
        )

        # Create a BOM for the product, with a single active component line
        self.bom = self.env["mrp.bom"].create(
            {
                "product_id": self.product.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "active": True,
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": self.env["product.product"]
                            .create(
                                {
                                    "name": "Component 1",
                                    "active": True,
                                }
                            )
                            .id,
                            "product_qty": 1.0,
                            "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                        }
                    )
                ],
            }
        )

        # Create a sale order with one order line using the product & BOM
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "bom_id": self.bom.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )

    def test_initial_state(self):
        """
        Test that a fresh order with active product & BOM
        has no archive flags set.
        """
        self.assertFalse(self.sale_order.has_archived_products_or_boms)
        self.assertFalse(self.sale_order.order_line[0].is_archived_or_bom_archived)

    def test_archive_product_triggers_flag(self):
        """
        Archiving the product should set archive flags on:
          - The sale order (`has_archived_products_or_boms`)
          - The corresponding order line (`is_archived_or_bom_archived`)
        """

        # Archive the product
        self.product.write({"active": False})

        # Force re-computation of computed fields in the current transaction
        self.sale_order.invalidate_recordset(["has_archived_products_or_boms"])
        self.sale_order.order_line.invalidate_recordset(["is_archived_or_bom_archived"])

        # Validate that both order and line are flagged
        self.assertTrue(self.sale_order.has_archived_products_or_boms)
        self.assertTrue(self.sale_order.order_line[0].is_archived_or_bom_archived)

    def test_archive_bom_triggers_flag(self):
        """
        Archiving the BOM (while keeping the product active)
        should also set archive flags on:
          - The sale order
          - The order line
        """

        # Archive the BOM
        self.bom.write({"active": False})

        # Force re-computation of computed fields
        self.sale_order.invalidate_recordset(["has_archived_products_or_boms"])
        self.sale_order.order_line.invalidate_recordset(["is_archived_or_bom_archived"])

        # Validate that both order and line are flagged
        self.assertTrue(self.sale_order.has_archived_products_or_boms)
        self.assertTrue(self.sale_order.order_line[0].is_archived_or_bom_archived)

    def test_copy_order_logs_archive_changes(self):
        """
        If a sale order with archived product is copied:
          - A chatter message should be posted on the new order
            indicating the product was archived.
        """

        # Step 1: Archive product
        self.product.write({"active": False})

        # Step 2: Copy the sale order
        new_order = self.sale_order.copy()

        # Step 3: Verify that chatter contains 'was archived' message
        messages = new_order.message_ids.mapped("body")
        self.assertTrue(any("was archived" in m for m in messages))
