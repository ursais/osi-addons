# Import Odoo libs
from odoo.tests import common, tagged
from datetime import date, timedelta
from odoo.fields import Command


@tagged("-at_install", "post_install")
class TestStockWarranty(common.TransactionCase):
    """
    TestStockWarranty
    =================

    This test case verifies that the warranty expiration date is correctly set
    on a stock lot when a delivery order is validated for a product with a
    warranty period.
    """

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        # Creating warranty attribute with values 1, 2, and 3
        self.size_attribute = self.env["product.attribute"].create(
            {
                "name": "Warranty",
                "value_ids": [
                    Command.create({"name": "1"}),
                    Command.create({"name": "2"}),
                    Command.create({"name": "3"}),
                ],
            }
        )
        (
            self.warranty_attribute_1,
            self.warranty_attribute_2,
            self.warranty_attribute_3,
        ) = self.size_attribute.value_ids

        # Create a product with a 2-year warranty and attribute lines
        self.product_template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "type": "service",
                "tracking": "serial",
                "warranty_period": "2",  # 2 years
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": self.size_attribute.id,
                            "value_ids": [
                                Command.set(
                                    [
                                        self.warranty_attribute_1.id,
                                        self.warranty_attribute_2.id,
                                        self.warranty_attribute_3.id,
                                    ]
                                )
                            ],
                        }
                    )
                ],
            }
        )
        self.product = self.product_template.product_variant_ids[0]

        # Assign product to warranty attributes (if necessary for logic)
        self.warranty_attribute_1.write({"product_id": self.product.id})
        self.warranty_attribute_2.write({"product_id": self.product.id})
        self.warranty_attribute_3.write({"product_id": self.product.id})

        # Create a lot/serial number for the product
        self.lot = self.env["stock.lot"].create(
            {
                "name": "SN001",
                "product_id": self.product.id,
            }
        )

        # Create a delivery order with a stock move
        self.picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "scheduled_date": date.today(),
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Move",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
            }
        )

        # Add move line with the lot and mark it as done
        self.move_line = self.env["stock.move.line"].create(
            {
                "picking_id": self.picking.id,
                "move_id": self.picking.move_ids[0].id,
                "product_id": self.product.id,
                "quantity": 1,
                "qty_done": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "lot_id": self.lot.id,
            }
        )

    def test_warranty_expiration_date_set_on_validate(self):
        """Check that warranty expiration is correctly set upon validation."""
        self.picking.with_context(override_ex=True).button_validate()

        expected_expiration = date.today() + timedelta(days=2 * 365)
        self.assertEqual(self.lot.warranty_expiration_date, expected_expiration)
