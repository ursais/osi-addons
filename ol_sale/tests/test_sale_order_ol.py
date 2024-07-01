from odoo.exceptions import ValidationError
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.customer = cls.env.ref("hr.work_contact_mit")
        cls.product = cls.env.ref("product.product_product_6")

    def test_action_confirm_ValidationError(self):
        """
        Test to ensure that Validation Error is raised
        when original request date is missing
        """
        # Without original_request_date
        sale_wo_original_request_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "pricelist_id": self.customer.property_product_pricelist.id,
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
            }
        )
        # With original_request_date
        sale_w_original_request_date = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "original_request_date": "2024-06-12",
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
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
            }
        )
        with self.assertRaises(ValidationError):
            sale_wo_original_request_date.action_confirm()
        try:
            sale_w_original_request_date.action_confirm()
        except ValidationError:
            self.fail("action_confirm() raised ValidationError unexpectedly!")
