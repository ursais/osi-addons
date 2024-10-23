from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestAttributeValue(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up test data: create companies and products
        cls.company1 = cls.env.ref("ol_base.onlogic_eu")
        cls.company2 = cls.env.ref("base.main_company")
        cls.product = cls.env["product.template"].create({"name": "Test Product"})

        cls.attribute_value1 = cls.env["product.attribute.value"].create(
            {
                "name": "Attribute Value 1",
                "product_id": cls.product.id,
                "company_ids": [(6, 0, [cls.company1.id])],
            }
        )

        cls.attribute_value2 = cls.env["product.attribute.value"].create(
            {
                "name": "Attribute Value 2",
                "product_id": cls.product.id,
                "company_ids": [(6, 0, [cls.company2.id])],
            }
        )

    def test_name_search_with_company_ids(self):
        # Test that name_search filters results based on company_ids
        with self.env.context(wizard_id=True):
            # Set logged-in company to company1
            self.env.company = self.company1

            result = self.attribute_value1.name_search(name="Attribute", limit=10)
            self.assertEqual(
                len(result), 1, "Only Attribute Value 1 should be returned."
            )
            self.assertEqual(result[0][1], "Attribute Value 1")

            # Change logged-in company to company2
            self.env.company = self.company2
            result = self.attribute_value1.name_search(name="Attribute", limit=10)
            self.assertEqual(
                len(result), 0, "No attribute values should be returned for company2."
            )

    def test_web_search_read_with_company_ids(self):
        # Test that web_search_read filters results based on company_ids
        with self.env.context(wizard_id=True):
            # Set logged-in company to company1
            self.env.company = self.company1

            domain = []
            result = self.attribute_value1.web_search_read(
                domain, specification={}, limit=10
            )
            self.assertEqual(
                len(result["records"]), 1, "Only Attribute Value 1 should be returned."
            )
            self.assertEqual(result["records"][0]["id"], self.attribute_value1.id)

            # Change logged-in company to company2
            self.env.company = self.company2
            result = self.attribute_value1.web_search_read(
                domain, specification={}, limit=10
            )
            self.assertEqual(
                len(result["records"]),
                0,
                "No attribute values should be returned for company2.",
            )
