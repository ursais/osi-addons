# Import Odoo libs
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestScrapOrder(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Initialize stock and customer locations using existing Odoo records
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        # Set up product categories for use in the test
        cls.categ_1 = cls.env.ref("product.product_category_all")
        cls.categ_2 = cls.env["product.category"].create({"name": "Test category"})

        # Create a virtual location to represent non-physical locations
        stock_location_locations_virtual = cls.env["stock.location"].create(
            {"name": "Virtual Locations", "usage": "view", "posz": 1}
        )

        # Initialize the scrap model for creating scrap orders
        cls.stock_scrap = cls.env["stock.scrap"]

        # Create a scrapped location that will be used in the tests
        cls.scrapped_location = cls.env["stock.location"].create(
            {
                "name": "Scrapped",
                "location_id": stock_location_locations_virtual.id,
                "scrap_location": True,
                "usage": "inventory",
            }
        )

        # Create a test product for the scrap operation
        cls.scrap_product = cls.env["product.product"].create(
            {
                "name": "Scrap Product A",
                "type": "product",
                "categ_id": cls.categ_1.id,
            }
        )

        # Create a reason code for the scrap operation
        cls.reason_code = cls.env["scrap.reason.code"].create(
            {
                "name": "DM300",
                "description": "Product is damage",
                "location_id": cls.scrapped_location.id,
            }
        )

    # Test method to ensure the correct scrap location is set
    def test_scrap_location_id(self):
        # Create a scrap order with the specified product, quantity, and reason
        self.scrap_order_id = self.stock_scrap.create(
            {
                "product_id": self.scrap_product.id,
                "scrap_qty": 1.00,
                "reason_code_id": self.reason_code.id,
            }
        )

        # Verify that the correct scrap location is selected in the scrap order
        self.assertEqual(
            self.scrap_order_id.scrap_location_id.id,
            self.scrapped_location.id,
            "Wrong scrap location selected.",
        )
