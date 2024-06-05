from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.company1 = cls.env.ref("stock.res_company_1")
        cls.company2 = cls.env.ref("base.main_company")
        cls.delivery1 = cls.env.ref("delivery.free_delivery_carrier")
        cls.delivery2 = cls.env.ref("delivery.delivery_carrier")

        cls.product0 = cls.env["product.template"].create(
            {"name": "Product for test", "list_price": 120.00, "weight": 1,}
        )
        cls.product1 = cls.env["product.template"].create(
            {
                "name": "Product for test 1",
                "list_price": 120.00,
                "weight": 1,
                "company_id": cls.company1.id,
            }
        )

        cls.product2 = cls.env["product.template"].create(
            {
                "name": "Product for test 2",
                "list_price": 120.00,
                "weight": 1,
                "company_id": cls.company2.id,
            }
        )

    def test_action_confirm_ValidationError(self):
        carrier_multiplier0 = self.env["delivery.carrier.multiplier"].create(
            {"carrier_id": self.delivery1.id, "multiplier": 10,}
        )
        self.product0.write({"carrier_multiplier_id": carrier_multiplier0.id})
        self.product0._compute_default_shipping_cost()

        carrier_multiplier1 = self.env["delivery.carrier.multiplier"].create(
            {
                "company_id": self.company1.id,
                "carrier_id": self.delivery1.id,
                "multiplier": 20,
            }
        )
        self.product1.write({"carrier_multiplier_id": carrier_multiplier1.id})
        self.product1._compute_default_shipping_cost()

        carrier_multiplier2 = self.env["delivery.carrier.multiplier"].create(
            {
                "company_id": self.company2.id,
                "carrier_id": self.delivery1.id,
                "multiplier": 30,
            }
        )
        self.product2.write({"carrier_multiplier_id": carrier_multiplier2.id})
        self.product2._compute_default_shipping_cost()
