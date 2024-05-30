from odoo.exceptions import ValidationError
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        # Get sale order model
        cls.so_model = cls.env.ref("sale.model_sale_order")
        cls.env.company.country_id = cls.env.ref("base.us")
        cls.env.ref("base.main_company").currency_id = cls.env.ref("base.USD")
        cls.currency = cls.env.ref("base.USD")

        dummy_product = cls.env["product.product"].create(
            [{"name": "Test product", "list_price": 500,}]
        )
        # Create users
        group_ids = (
            cls.env.ref("base.group_system")
            + cls.env.ref("sales_team.group_sale_salesman_all_leads")
        ).ids
        cls.test_user_1 = cls.env["res.users"].create(
            {
                "name": "John",
                "login": "test1",
                "groups_id": [(6, 0, group_ids)],
                "email": "test@examlple.com",
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Partner for test"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product for test", "list_price": 120.00}
        )

    def test_action_confirm_ValidationError(self):
        # Without original_request_date
        sale_wo_original_request_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
                "pricelist_id": self.customer.property_product_pricelist.id,
            }
        )
        # Without original_request_date
        sale_w_original_request_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "original_request_date": "2024-06-12",
                "commitment_date": "2024-06-10",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
                "pricelist_id": self.customer.property_product_pricelist.id,
            }
        )
        with self.assertRaises(ValidationError):
            sale_wo_original_request_date.action_confirm()
        sale_w_original_request_date.action_confirm()
