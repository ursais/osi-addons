from odoo.addons.product_configurator.tests import (
    test_product_configurator_test_cases as TC,
)


class SaleOrder(TC.ProductConfiguratorTestCases):

    def setUp(self):
        super().setUp()

        # Initialize the SaleOrderTemplate model
        self.SaleOrderTemplateId = self.env["sale.order.template"]

        # Get the partner of the current user
        self.resPartner = self.env.user.partner_id

    def test_00_reconfigure_product(self):

        # Test case for reconfiguring a product in a sale order

        # Step 1: Create a Quotation Template
        quotation_template = self.SaleOrderTemplateId.create(
            {
                "name": "Test Quotation Template",  # Provide a name for the template
            }
        )

        # Prepare the context for the product configurator wizard
        context = dict(
            default_order_id=quotation_template.id,
            wizard_model="product.configurator.sale.order.temp",
        )

        # Initialize the product configurator wizard with the prepared context
        self.ProductConfWizard = self.env[
            "product.configurator.sale.order.temp"
        ].with_context(**context)

        # Start the configuration process
        quotation_template.action_config_start()

        # Custom method to move to the next step in the configuration process
        self._configure_product_nxt_step()

        # Reconfigure the product in the template lines
        quotation_template.sale_order_template_line_ids.reconfigure_product()

        # Get the product template related to the reconfigured product
        product_tmpl = (
            quotation_template.sale_order_template_line_ids.product_id.product_tmpl_id
        )

        # Verify that the product template matches the configured product
        self.assertEqual(
            product_tmpl.id,
            self.config_product.id,
            "Error: If product_tmpl not exists\
            Method: action_config_start()",
        )

        # Step 2: Create a Sale Order using the created Quotation Template
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.resPartner.id,
                "pricelist_id": self.resPartner.property_product_pricelist.id,
                "sale_order_template_id": quotation_template.id,
            }
        )

        # Trigger the onchange event to apply the template to the sale order
        sale_order._onchange_sale_order_template_id()

        # Retrieve the sale order line and template line for comparison
        sale_order_line = sale_order.order_line
        sale_order_template_line = quotation_template.sale_order_template_line_ids

        # Verify that the product template IDs match between the order line and
        # the template line
        self.assertEqual(sale_order_line.product_template_id.id, product_tmpl.id)

        # Verify that the configuration session IDs match between the order line and
        # the template line
        self.assertEqual(
            sale_order_template_line.config_session_id.id,
            sale_order_line.config_session_id.id,
        )

        # Verify that the configuration status (config_ok) matches between the order
        # line and the template line
        self.assertEqual(sale_order_template_line.config_ok, sale_order_line.config_ok)
