from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestProductConfigStock(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        # Set up the testing environment by initializing required records.
        super().setUpClass()

        # Create a product template for an "i7 Processor".
        cls.test_i7_pro = cls.env["product.template"].create(
            {
                "name": "i7 Processor",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        # Create a product attribute named "SSD" with two values: "SSD-512GB" and
        # "SSD-1TB".
        cls.attr_ssd = cls.env["product.attribute"].create(
            {
                "name": "SSD",
                "value_ids": [
                    (0, 0, {"name": "SSD-512GB"}),
                    (0, 0, {"name": "SSD-1TB"}),
                ],
            }
        )

        # Create an additional attribute value "SSD-256GB" under the "SSD" attribute
        # and set the context to show the price extra in the display name.
        cls.value_ssd256 = (
            cls.env["product.attribute.value"]
            .with_context(show_price_extra=True)
            .create({"name": "SSD-256GB", "attribute_id": cls.attr_ssd.id})
        )

        # Create a product attribute named "Processor" with three
        # values: "i3", "i5", and "i7".
        cls.attr_processor = cls.env["product.attribute"].create(
            {
                "name": "Processor",
                "value_ids": [
                    (0, 0, {"name": "i3"}),
                    (0, 0, {"name": "i5"}),
                ],
            }
        )

        # Create an attribute value "i7" under the "Processor" attribute and link
        # it to the "i7 Processor" product variant.
        # The context is set to show the price extra in the display name.
        cls.attr_i7_value = (
            cls.env["product.attribute.value"]
            .with_context(show_price_extra=True)
            .create(
                {
                    "name": "i7",
                    "attribute_id": cls.attr_processor.id,
                    "product_id": cls.test_i7_pro.product_variant_id.id,
                }
            )
        )

    def test_01_check_attribute_value_display_name(self):
        # Test the display name for an attribute value that is linked to a product.
        self.assertEqual(
            self.attr_i7_value.display_name,
            "i7 ( +1.00 ) (A:0/OH:0.0) (In Development)",
        )

        # Test the display name for an attribute value that is not linked to a product.
        self.assertEqual(self.value_ssd256.display_name, "SSD: SSD-256GB")
