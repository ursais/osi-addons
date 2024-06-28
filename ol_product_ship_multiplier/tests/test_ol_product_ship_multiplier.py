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
        cls.product0 = cls.env.ref("product.product_product_4_product_template")
        cls.carrier_multiplier0 = cls.env.ref("ol_product_ship_multiplier.carrier_multiplier0")
        cls.carrier_multiplier1 = cls.env.ref("ol_product_ship_multiplier.carrier_multiplier1")
        cls.carrier_multiplier2 = cls.env.ref("ol_product_ship_multiplier.carrier_multiplier2")

    def test_action_confirm_ValidationError(self):
        """
            Tests to ensure shipping cost is correctly calculated
            First product should end with a shipping cost of 10
            Second product should end with a shipping cost of 20
            Third product should end with a shipping cost of 30
        """
        self.product0.write({"carrier_multiplier_id": self.carrier_multiplier0.id})
        self.product0._compute_default_shipping_cost()
        expected_shipping_cost0 = self.product0.weight * self.carrier_multiplier0.multiplier
        self.assertEqual(self.product0.default_shipping_cost, expected_shipping_cost0)

        self.product0.write({"carrier_multiplier_id": self.carrier_multiplier1.id})
        self.product0._compute_default_shipping_cost()
        expected_shipping_cost1 = self.product0.weight * self.carrier_multiplier1.multiplier
        self.assertEqual(self.product0.default_shipping_cost, expected_shipping_cost1)

        self.product0.write({"carrier_multiplier_id": self.carrier_multiplier2.id})
        self.product0._compute_default_shipping_cost()
        expected_shipping_cost2 = self.product0.weight * self.carrier_multiplier2.multiplier
        self.assertEqual(self.product0.default_shipping_cost, expected_shipping_cost2)
