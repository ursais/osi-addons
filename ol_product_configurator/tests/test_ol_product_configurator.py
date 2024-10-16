from odoo.tests import common, tagged, Form
from odoo.exceptions import ValidationError
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestAttributeValue(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.env.user.groups_id += cls.env.ref("uom.group_uom")
        # Required for `product_id ` to be visible in the view
        cls.env.user.groups_id += cls.env.ref("product.group_product_variant")
        cls.Product = cls.env["product.product"]
        cls.company1 = cls.env.ref("ol_base.onlogic_eu")
        cls.USCompany = cls.env.ref("base.main_company")

    def test_00_check_company_ids(self):
        self.olive_color_product = self.Product.create(
            {
                "name": "Olive Color",
                "detailed_type": "product",
                "company_id": self.company1.id,
            }
        )

        # ProductAttribute
        self.attr_test = self.env["product.attribute"].create(
            {
                "name": "Test-Color",
                "value_ids": [
                    (0, 0, {"name": "Black-Color"}),
                    (0, 0, {"name": "Red Color"}),
                ],
            }
        )

        # ProductAttributeValue
        with self.assertRaises(ValidationError):
            self.value_olive_color = self.env["product.attribute.value"].create(
                [
                    {
                        "name": "Olive Color",
                        "attribute_id": self.attr_test.id,
                        "product_id": self.olive_color_product.id,
                        "company_id": self.USCompany.id,
                    }
                ]
            )
