from odoo.exceptions import UserError

from ..tests.common import ProductConfiguratorTestCases

# FIXME: many tests here do not have any assertions.
# They simply run something and expect it to not raise an exception.
# This is not a good practice. Tests should have assertions.


class ConfigurationWizard(ProductConfiguratorTestCases):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.productTemplate = cls.env["product.template"]
        cls.productAttributeLine = cls.env["product.template.attribute.line"]
        cls.productConfigStepLine = cls.env["product.config.step.line"]
        cls.productConfigSession = cls.env["product.config.session"]
        cls.product_category = cls.env.ref("product.product_category_5")
        cls.attr_line_fuel = cls.env.ref(
            "product_configurator.product_attribute_line_2_series_fuel"
        )
        cls.attr_line_engine = cls.env.ref(
            "product_configurator.product_attribute_line_2_series_engine"
        )
        cls.value_diesel = cls.env.ref(
            "product_configurator.product_attribute_value_diesel"
        )
        cls.value_218d = cls.env.ref(
            "product_configurator.product_attribute_value_218d"
        )
        cls.value_220d = cls.env.ref(
            "product_configurator.product_attribute_value_220d"
        )
        cls.value_silver = cls.env.ref(
            "product_configurator.product_attribute_value_silver"
        )
        cls.config_step_engine = cls.env.ref("product_configurator.config_step_engine")
        cls.config_step_body = cls.env.ref("product_configurator.config_step_body")
        cls.product_tmpl_id = cls.env["product.template"].create(
            {
                "name": "Test Configuration",
                "config_ok": True,
                "type": "consu",
                "categ_id": cls.product_category.id,
            }
        )
        cls.custom_vals = cls.productConfigSession.get_custom_value_id()
        cls.cfg_tmpl = cls.env.ref("product_configurator.bmw_2_series")

        attribute_vals = cls.cfg_tmpl.attribute_line_ids.mapped("value_ids")
        cls.attr_vals = attribute_vals

        cls.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().items()
        }

    def _check_wizard_nxt_step(self):
        self.ProductConfWizard.action_next_step()
        product_config_wizard = self.ProductConfWizard.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
            }
        )
        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "attribute_id": self.attr_fuel.id,
                "value_ids": [(6, 0, [self.value_gasoline.id, self.value_diesel.id])],
                "required": True,
            }
        )
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "attribute_id": self.attr_engine.id,
                "value_ids": [(6, 0, [self.value_218i.id, self.value_220i.id])],
                "required": True,
            }
        )
        # create attribute line 2
        self.attributeLine3 = self.productAttributeLine.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "attribute_id": self.attr_engine.id,
                "value_ids": [(6, 0, [self.value_218d.id, self.value_220d.id])],
                "required": True,
            }
        )
        # configure product creating config step
        self.configStepLine1 = self.productConfigStepLine.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "config_step_id": self.config_step_engine.id,
                "attribute_line_ids": [
                    (6, 0, [self.attributeLine1.id, self.attributeLine2.id])
                ],
            }
        )
        # create config_step_line 2
        self.configStepLine2 = self.productConfigStepLine.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "config_step_id": self.config_step_body.id,
                "attribute_line_ids": [(6, 0, [self.attributeLine3.id])],
            }
        )
        self.product_tmpl_id.write(
            {
                "config_step_line_ids": [
                    (6, 0, [self.configStepLine1.id, self.configStepLine2.id])
                ],
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{self.attr_fuel.id}": self.value_gasoline.id,
                f"__attribute_{self.attr_engine.id}": self.value_218i.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{self.attr_color.id}": self.value_red.id,
            }
        )
        return product_config_wizard

    def test_01_action_previous_step(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.action_previous_step()
        self.assertEqual(
            product_config_wizard.state,
            str(self.configStepLine1.id),
            "Error: If state are not equal\
            Method: action_next_step()",
        )
        product_config_wizard.action_next_step()
        self.assertEqual(
            product_config_wizard.state,
            str(self.configStepLine2.id),
            "Error: If state are not equal\
            Method: action_next_step()",
        )
        wizard_action = product_config_wizard.action_next_step()
        variant_id2 = wizard_action.get("res_id")
        self.assertTrue(
            variant_id2,
            "Error: If varient not exists\
            Method: action_next_step()",
        )

    def test_02_action_reset(self):
        product_config_wizard = self._check_wizard_nxt_step()
        action_wizard = product_config_wizard.action_reset()
        product_tmpl_id = action_wizard.get("context")
        self.assertTrue(
            product_tmpl_id.get("default_product_tmpl_id"),
            "Error: If product_tmpl_id not exists\
            Method: action_reset()",
        )

    def test_03_compute_attr_lines(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._compute_attr_lines()
        self.assertTrue(
            product_config_wizard.attribute_line_ids,
            "Error: If atttribute_line_ids not exists\
            Method: _compute_attr_lines()",
        )

    def test_04_get_state_selection(self):
        product_config_wizard = self._check_wizard_nxt_step()
        config_wiz = product_config_wizard.with_context(
            wizard_id=product_config_wizard.id
        ).get_state_selection()
        self.assertTrue(
            config_wiz[1:],
            "Error: If not config step selection\
            Method: get_state_selection()",
        )

    def test_05_compute_cfg_image(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._compute_cfg_image()
        self.assertFalse(
            product_config_wizard.product_img,
            "Error: If product_img exists\
            Method: _compute_cfg_image()",
        )

    def test_06_onchange_product_tmpl(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.write(
            {
                "product_tmpl_id": self.config_product.id,
            }
        )
        with self.assertRaises(UserError):
            product_config_wizard.onchange_product_tmpl()

    def test_07_get_onchange_domains(self):
        product_config_wizard = self._check_wizard_nxt_step()

        values = [
            "gasoline",
            "228i",
            "model_luxury_line",
            "silver",
            "rims_384",
            "tapistry_black",
            "steptronic",
            "smoker_package",
            "tow_hook",
        ]
        product_config_wizard.get_onchange_domains(values)

    def test_08_onchange_state(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._onchange_state()

    def test_09_onchange_product_preset(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._onchange_product_preset()

    def test_10_open_step(self):
        wizard = self.env["product.configurator"]
        step_to_open = wizard.config_session_id.check_and_open_incomplete_step()
        wizard.open_step(step_to_open)

    # FIXME: broken test
    # Fails at `product_config_wizard.attribute_line_ids.update(` as
    #     """odoo.exceptions.UserError:
    #     On the product Test Configuration
    #     you cannot transform the attribute Engine into the attribute 5."""
    #
    # Also, the test is not very useful. It does not assert anything.
    #
    # def test_11_onchange(self):
    #     field_name = ""
    #     values = {f"__attribute_{self.attr_fuel.id}": self.value_gasoline.id}
    #     product_config_wizard = self._check_wizard_nxt_step()
    #     field_prefix = product_config_wizard._prefixes.get("field_prefix")
    #     field_name = f"{field_prefix}{field_name}"
    #     specs = product_config_wizard._onchange_spec()
    #     product_config_wizard.onchange(values, field_name, specs)
    #
    #     product_config_wizard.attribute_line_ids.update(
    #         {
    #             "attribute_id": self.attr_fuel.id,
    #             "custom": True,
    #         }
    #     )
    #     values2 = {
    #         f"__attribute_{self.attr_fuel.id}": self.custom_vals.id,
    #         f"__custom_{self.attr_fuel.id}": "Test1",
    #     }
    #     product_config_wizard.onchange(values2, field_name, specs)

    def test_12_fields_get(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.fields_get()
        product_config_wizard.with_context(
            wizard_id=product_config_wizard.id
        ).fields_get()

        # custom value
        self.attr_line_fuel.custom = True
        self.attr_line_engine.custom = True
        product_config_wizard_1 = self.ProductConfWizard.create(
            {
                "product_tmpl_id": self.config_product.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_fuel.id}": self.value_gasoline.id,
                f"__custom_{self.attr_fuel.id}": "Test1",
                f"__attribute_{self.attr_engine.id}": self.value_218i.id,
                f"__custom_{self.attr_engine.id}": "Test2",
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_color.id}": self.value_red.id,
                f"__attribute_{self.attr_rims.id}": self.value_rims_378.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_model_line.id}": self.value_sport_line.id,
            }
        )
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_engine.id}": self.value_220i.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.action_next_step()

        vals = {
            f"__attribute_{self.attr_model_line.id}": self.value_model_sport_line.id,
        }
        product_config_wizard_1.write(vals)
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_tapistry.id}": self.value_tapistry.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_transmission.id}": self.value_transmission.id,
                f"__attribute_{self.attr_options.id}": [
                    [6, 0, [self.value_options_2.id]]
                ],
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.with_context(
            wizard_id=product_config_wizard_1.id
        ).fields_get()

    def test_13_get_view(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.get_view()
        product_config_wizard.with_context(
            wizard_id=product_config_wizard.id
        ).get_view()
        # custom value
        # custom value
        self.attr_line_fuel.custom = True
        self.attr_line_engine.custom = True
        product_config_wizard_1 = self.ProductConfWizard.create(
            {
                "product_tmpl_id": self.config_product.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_fuel.id}": self.value_gasoline.id,
                f"__custom_{self.attr_fuel.id}": "Test1",
                f"__attribute_{self.attr_engine.id}": self.value_218i.id,
                f"__custom_{self.attr_engine.id}": "Test2",
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_color.id}": self.value_red.id,
                f"__attribute_{self.attr_rims.id}": self.value_rims_378.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_model_line.id}": self.value_sport_line.id,
            }
        )
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_engine.id}": self.value_220i.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.action_next_step()
        vals = {
            f"__attribute_{self.attr_model_line.id}": self.value_model_sport_line.id,
        }
        product_config_wizard_1.write(vals)
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_tapistry.id}": self.value_tapistry.id,
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_transmission.id}": self.value_transmission.id,
                f"__attribute_{self.attr_options.id}": [
                    [6, 0, [self.value_options_2.id]]
                ],
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.with_context(
            wizard_id=product_config_wizard_1.id
        ).get_view()

    def test_14_unlink(self):
        product_config_wizard = self._check_wizard_nxt_step()
        unlinkWizard = product_config_wizard.unlink()
        self.assertTrue(
            unlinkWizard,
            "Error: If not unlink record\
            Method: unlink()",
        )

    def test_15_read(self):
        product_config_wizard = self._check_wizard_nxt_step()
        values = {
            f"__attribute_{self.attr_fuel.id}": self.value_gasoline.id,
            f"__attribute_{self.attr_engine.id}": self.value_218i.id,
            f"__attribute_{self.attr_color.id}": self.value_red.id,
        }
        product_config_wizard.read(values)
        product_tmpl = self.env["product.template"].create(
            {
                "name": "Test Custom",
                "config_ok": True,
                "type": "consu",
                "categ_id": self.product_category.id,
            }
        )
        self.ProductConfWizard.action_next_step()
        product_config_wizard_1 = self.ProductConfWizard.create(
            {
                "product_tmpl_id": product_tmpl.id,
            }
        )
        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "attribute_id": self.attr_fuel.id,
                "value_ids": [(6, 0, [self.value_gasoline.id, self.value_diesel.id])],
                "required": True,
                "custom": True,
            }
        )
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "attribute_id": self.attr_engine.id,
                "value_ids": [(6, 0, [self.value_218i.id, self.value_220i.id])],
                "required": True,
                "custom": True,
            }
        )
        # create attribute line 2
        self.attributeLine3 = self.productAttributeLine.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "attribute_id": self.attr_engine.id,
                "value_ids": [(6, 0, [self.value_218d.id, self.value_220d.id])],
                "required": True,
            }
        )
        # configure product creating config step
        self.configStepLine1 = self.productConfigStepLine.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "config_step_id": self.config_step_engine.id,
                "attribute_line_ids": [
                    (6, 0, [self.attributeLine1.id, self.attributeLine2.id])
                ],
            }
        )
        # create config_step_line 2
        self.configStepLine2 = self.productConfigStepLine.create(
            {
                "product_tmpl_id": product_tmpl.id,
                "config_step_id": self.config_step_body.id,
                "attribute_line_ids": [(6, 0, [self.attributeLine3.id])],
            }
        )
        product_tmpl.write(
            {
                "config_step_line_ids": [
                    (6, 0, [self.configStepLine1.id, self.configStepLine2.id])
                ],
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_fuel.id}": self.custom_vals.id,
                f"__custom_{self.attr_fuel.id}": "#DEFSRE",
                f"__attribute_{self.attr_engine.id}": self.custom_vals.id,
                f"__custom_{self.attr_engine.id}": "#FERDFGR",
            }
        )
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write(
            {
                f"__attribute_{self.attr_color.id}": self.value_red.id,
            }
        )
        # check for custom value
        custom_vals = {
            f"__attribute_{self.attr_fuel.id}": self.custom_vals.id,
            f"__custom_{self.attr_fuel.id}": "#DEFSRE",
            f"__attribute_{self.attr_engine.id}": self.custom_vals.id,
            f"__custom_{self.attr_engine.id}": "#FERDFGR",
            f"__attribute_{self.attr_color.id}": self.value_red.id,
        }
        product_config_wizard_1.read(custom_vals)
        session = self.productConfigSession.search(
            [("product_tmpl_id", "=", product_tmpl.id)]
        )
        session.unlink()
        self.attributeLine1.custom = False
        self.attributeLine1.multi = True
        self.ProductConfWizard.action_next_step()
        product_config_wizard_2 = self.ProductConfWizard.create(
            {
                "product_tmpl_id": product_tmpl.id,
            }
        )
        product_config_wizard_2.action_next_step()
        product_config_wizard_2.write(
            {
                f"__attribute_{self.attr_fuel.id}": [
                    (6, 0, [self.value_diesel.id, self.value_gasoline.id])
                ],
                f"__attribute_{self.attr_engine.id}": self.custom_vals.id,
                f"__custom_{self.attr_engine.id}": "#FERDFGR",
            }
        )
        product_config_wizard_2.action_next_step()
        product_config_wizard_2.write(
            {
                f"__attribute_{self.attr_color.id}": self.value_red.id,
            }
        )
        # check for multi value
        multi_vals = {
            f"__attribute_{self.attr_fuel.id}": [
                (6, 0, [self.value_diesel.id, self.value_gasoline.id])
            ],
            f"__attribute_{self.attr_engine.id}": self.custom_vals.id,
            f"__custom_{self.attr_engine.id}": "#FERDFGR",
            f"__attribute_{self.attr_color.id}": self.value_red.id,
        }
        product_config_wizard_2.read(multi_vals)

    def test_16_get_onchange_domains(self):
        self.wizard = self.env["product.configurator"]
        # session id
        session_id = self.productConfigSession.create(
            {
                "product_tmpl_id": self.config_product.id,
                "value_ids": [
                    (
                        6,
                        0,
                        [
                            self.value_gasoline.id,
                            self.value_transmission.id,
                            self.value_red.id,
                        ],
                    )
                ],
                "user_id": self.env.user.id,
            }
        )
        field_prefix = self.wizard._prefixes.get("field_prefix")
        values_ids = self.value_diesel.ids
        product_tmpl_id = self.config_product
        domains_available = self.wizard.get_onchange_domains(
            values_ids, product_tmpl_id, session_id
        )
        rec = domains_available[
            field_prefix + str(self.value_sport_line.attribute_id.id)
        ][-1][-1]
        self.assertNotIn(
            self.value_sport_line.id,
            rec,
            "Error: If value exists\
            Method: get_onchange_domains()",
        )
