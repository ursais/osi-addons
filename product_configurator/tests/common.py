from odoo.addons.base.tests.common import BaseCommon


class ProductConfiguratorTestCases(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductConfWizard = cls.env["product.configurator"]
        cls.config_product = cls.env.ref("product_configurator.bmw_2_series")
        cls.product_category = cls.env.ref("product.product_category_5")
        # attributes
        cls.attr_fuel = cls.env.ref("product_configurator.product_attribute_fuel")
        cls.attr_engine = cls.env.ref("product_configurator.product_attribute_engine")
        cls.attr_color = cls.env.ref("product_configurator.product_attribute_color")
        cls.attr_rims = cls.env.ref("product_configurator.product_attribute_rims")
        cls.attr_model_line = cls.env.ref(
            "product_configurator.product_attribute_model_line"
        )
        cls.attr_tapistry = cls.env.ref(
            "product_configurator.product_attribute_tapistry"
        )
        cls.attr_transmission = cls.env.ref(
            "product_configurator.product_attribute_transmission"
        )
        cls.attr_options = cls.env.ref("product_configurator.product_attribute_options")

        # values
        cls.value_gasoline = cls.env.ref(
            "product_configurator.product_attribute_value_gasoline"
        )
        cls.value_218i = cls.env.ref(
            "product_configurator.product_attribute_value_218i"
        )
        cls.value_220i = cls.env.ref(
            "product_configurator.product_attribute_value_220i"
        )
        cls.value_red = cls.env.ref("product_configurator.product_attribute_value_red")
        cls.value_rims_378 = cls.env.ref(
            "product_configurator.product_attribute_value_rims_378"
        )
        cls.value_sport_line = cls.env.ref(
            "product_configurator.product_attribute_value_sport_line"
        )
        cls.value_model_sport_line = cls.env.ref(
            "product_configurator.product_attribute_value_model_sport_line"
        )
        cls.value_tapistry = cls.env.ref(
            "product_configurator.product_attribute_value_tapistry" + "_oyster_black"
        )
        cls.value_transmission = cls.env.ref(
            "product_configurator.product_attribute_value_steptronic"
        )
        cls.value_options_1 = cls.env.ref(
            "product_configurator.product_attribute_value_smoker_package"
        )
        cls.value_options_2 = cls.env.ref(
            "product_configurator.product_attribute_value_sunroof"
        )

    @classmethod
    def _configure_product_nxt_step(cls):
        product_config_wizard = cls.ProductConfWizard.create(
            {
                "product_tmpl_id": cls.config_product.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_fuel.id}": cls.value_gasoline.id,
                f"__attribute_{cls.attr_engine.id}": cls.value_218i.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_color.id}": cls.value_red.id,
                f"__attribute_{cls.attr_rims.id}": cls.value_rims_378.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_model_line.id}": cls.value_sport_line.id,
            }
        )
        product_config_wizard.action_previous_step()
        product_config_wizard.action_previous_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_engine.id}": cls.value_220i.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.action_next_step()
        vals = {
            f"__attribute_{cls.attr_model_line.id}": cls.value_model_sport_line.id,
        }
        product_config_wizard.write(vals)
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_tapistry.id}": cls.value_tapistry.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{cls.attr_transmission.id}": cls.value_transmission.id,
                f"__attribute_{cls.attr_options.id}": [
                    [6, 0, [cls.value_options_2.id]]
                ],
            }
        )

        return product_config_wizard.action_next_step()
