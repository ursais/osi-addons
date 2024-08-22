from datetime import date, timedelta

from odoo import fields

from odoo.addons.product_configurator.tests import (
    test_product_configurator_test_cases as TC,
)


class SaleOrder(TC.ProductConfiguratorTestCases):
    def setUp(self):
        super().setUp()
        self.SaleBlanketOrderId = self.env["sale.blanket.order"]
        self.productPricelist = self.env["product.pricelist"]
        self.mrpBom = self.env["mrp.bom"]
        self.resPartner = self.env.user.partner_id
        self.currency_id = self.env.ref("base.USD")
        self.ProductConfWizard = self.env["product.configurator.sale.blanket.order"]
        self.payment_term = self.env.ref("account.account_payment_term_immediate")
        self.tomorrow = date.today() + timedelta(days=1)

    def test_00_reconfigure_product(self):
        pricelist_id = self.productPricelist.create(
            {
                "name": "Test Pricelist",
                "currency_id": self.currency_id.id,
            }
        )
        sale_blanket_order_id = self.SaleBlanketOrderId.create(
            {
                "partner_id": self.resPartner.id,
                "pricelist_id": pricelist_id.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
            }
        )
        context = dict(
            default_order_id=sale_blanket_order_id.id,
            wizard_model="product.configurator.sale.blanket.order",
        )

        self.ProductConfWizard = self.env[
            "product.configurator.sale.blanket.order"
        ].with_context(**context)
        sale_blanket_order_id.action_config_start()
        self._configure_product_nxt_step()
        sale_blanket_order_id.line_ids.reconfigure_product()
        product_tmpl = sale_blanket_order_id.line_ids.product_id.product_tmpl_id
        self.assertEqual(
            product_tmpl.id,
            self.config_product.id,
            "Error: If product_tmpl not exsits\
            Method: action_config_start()",
        )
        self.assertFalse(sale_blanket_order_id.line_ids.mapped("bom_id"))

        # create bom
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "product_id": sale_blanket_order_id.line_ids.product_id.id,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        sale_blanket_order = self.SaleBlanketOrderId.create(
            {
                "partner_id": self.resPartner.id,
                "pricelist_id": pricelist_id.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
            }
        )
        context = dict(
            default_order_id=sale_blanket_order.id,
            wizard_model="product.configurator.sale.blanket.order",
        )
        self.ProductConfWizard = self.env[
            "product.configurator.sale.blanket.order"
        ].with_context(**context)
        sale_blanket_order.action_config_start()
        self._configure_product_nxt_step()
        sale_blanket_order.line_ids.reconfigure_product()
        self.assertTrue(sale_blanket_order.line_ids.mapped("bom_id"))
