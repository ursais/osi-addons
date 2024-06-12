from odoo.addons.product_configurator.tests import test_product_configurator_test_cases


class ProductRestrictionPolicy(
    test_product_configurator_test_cases.ProductConfiguratorTestCases
):
    def test_product_restriction_policy(self):
        """
        The test_product_restriction_policy function tests
        the values_available() method of the product.config.session model
        to ensure that it returns a list of available attribute values
        for a given set of selected attribute values and product template,
        based on the restriction policy defined in the product template.
        :return: A list of values that are not available
        """
        self.value_diesel = self.env.ref(
            "product_configurator.product_attribute_value_diesel"
        )
        self.productConfigSession = self.env["product.config.session"]
        check_available_val_ids = (
            self.value_gasoline + self.value_218i + self.value_sport_line
        ).ids
        product_tmpl_id = self.config_product.id
        self.config_product.write({"restriction_policy": "standard"})
        values_ids = [self.value_diesel.id]
        available_value_ids = self.productConfigSession.values_available(
            check_available_val_ids, values_ids, {}, product_tmpl_id
        )
        self.assertNotIn(
            self.value_sport_line.id,
            available_value_ids,
            "Error: If value exists  Method: values_available()",
        )
