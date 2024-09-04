from odoo.addons.product_configurator.tests import (
    test_product_configurator_test_cases as TC,
)


class SaleOrder(TC.ProductConfiguratorTestCases):
    def setUp(self):
        super().setUp()
        self.SaleOrderTemplateId = self.env["sale.order.template"]
        self.resPartner = self.env.user.partner_id

    def test_00_reconfigure_product(self):
        # Create Quotation Template
        quotation_template = self.SaleOrderTemplateId.create(
            {
                "name": "Test Quotation Template",
            }
        )

        context = dict(
            default_order_id=quotation_template.id,
            wizard_model="product.configurator.sale.order.temp",
        )

        self.ProductConfWizard = self.env[
            "product.configurator.sale.order.temp"
        ].with_context(**context)
        quotation_template.action_config_start()
        self._configure_product_nxt_step()

        quotation_template.sale_order_template_line_ids.reconfigure_product()
        product_tmpl = (
            quotation_template.sale_order_template_line_ids.product_id.product_tmpl_id
        )
        self.assertEqual(
            product_tmpl.id,
            self.config_product.id,
            "Error: If product_tmpl not exsits\
            Method: action_config_start()",
        )

        # Create Sale Order with Template
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.resPartner.id,
                "pricelist_id": self.resPartner.property_product_pricelist.id,
                "sale_order_template_id": quotation_template.id,
            }
        )
        sale_order._onchange_sale_order_template_id()
        sale_order_line = sale_order.order_line
        sale_order_template_line = quotation_template.sale_order_template_line_ids
        self.assertEqual(sale_order_line.product_template_id.id, product_tmpl.id)
        self.assertEqual(
            sale_order_template_line.config_session_id.id,
            sale_order_line.config_session_id.id,
        )
        self.assertEqual(sale_order_template_line.config_ok, sale_order_line.config_ok)
