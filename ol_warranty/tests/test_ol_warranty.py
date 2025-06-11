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
    def setUpClass(cls):
        super().setUpClass()

        # Create warranty attribute with values: 1 Year, 2 Years, 3 Years
        cls.warranty_attribute = cls.env["product.attribute"].create(
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
            cls.attr_value_1_year,
            cls.attr_value_2_years,
            cls.attr_value_3_years,
        ) = cls.warranty_attribute.value_ids

        # Create a product template with a 2-year warranty and attribute line
        cls.product_template_with_2yr_warranty = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "type": "service",
                "tracking": "serial",
                "warranty_period": "2",  # 2 years
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.warranty_attribute.id,
                            "value_ids": [
                                Command.set(
                                    [
                                        cls.attr_value_1_year.id,
                                        cls.attr_value_2_years.id,
                                        cls.attr_value_3_years.id,
                                    ]
                                )
                            ],
                        }
                    )
                ],
            }
        )

        # Use the first product variant
        cls.product_variant = (
            cls.product_template_with_2yr_warranty.product_variant_ids[0]
        )

        # Optionally associate attribute values with the product variant
        cls.attr_value_1_year.write({"product_id": cls.product_variant.id})
        cls.attr_value_2_years.write({"product_id": cls.product_variant.id})
        cls.attr_value_3_years.write({"product_id": cls.product_variant.id})

        # Create a serial/lot for the product
        cls.serial_lot_sn001 = cls.env["stock.lot"].create(
            {
                "name": "SN001",
                "product_id": cls.product_variant.id,
            }
        )

        # Create an outgoing delivery order with one stock move
        cls.delivery_order = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "scheduled_date": date.today(),
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Move",
                            "product_id": cls.product_variant.id,
                            "product_uom_qty": 1,
                            "product_uom": cls.product_variant.uom_id.id,
                            "location_id": cls.env.ref("stock.stock_location_stock").id,
                            "location_dest_id": cls.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
            }
        )

        # Add a move line for the lot and mark it as done
        cls.serial_move_line = cls.env["stock.move.line"].create(
            {
                "picking_id": cls.delivery_order.id,
                "move_id": cls.delivery_order.move_ids[0].id,
                "product_id": cls.product_variant.id,
                "quantity": 1,
                "qty_done": 1,
                "product_uom_id": cls.product_variant.uom_id.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "lot_id": cls.serial_lot_sn001.id,
            }
        )

    def test_warranty_expiration_date_set_on_validate(self):
        """Ensure warranty expiration is correctly set on lot after delivery validation."""
        self.delivery_order.with_context(override_ex=True).button_validate()

        expected_expiration = date.today() + timedelta(days=2 * 365)
        self.assertEqual(
            self.serial_lot_sn001.warranty_expiration_date,
            expected_expiration,
            "Warranty expiration date not correctly set based on 2-year warranty.",
        )
