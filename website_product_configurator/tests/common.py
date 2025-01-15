from datetime import timedelta

from odoo import fields

from odoo.addons.product_configurator.tests import common


class TestProductConfiguratorValues(common.ProductConfiguratorTestCases):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.productConfigStepLine = cls.env["product.config.step.line"]
        cls.productAttributeLine = cls.env["product.template.attribute.line"]
        cls.product_category = cls.env.ref("product.product_category_5")
        cls.value_diesel = cls.env.ref(
            "product_configurator.product_attribute_value_diesel"
        )
        cls.value_218d = cls.env.ref(
            "product_configurator.product_attribute_value_218d"
        )
        cls.value_220d = cls.env.ref(
            "product_configurator.product_attribute_value_220d"
        )
        cls.config_step_engine = cls.env.ref("product_configurator.config_step_engine")
        cls.product_tmpl_id = cls.env["product.template"].create(
            {
                "name": "Test Configuration",
                "config_ok": True,
                "type": "consu",
                "categ_id": cls.product_category.id,
            }
        )
        cls.attributeLine1 = cls.productAttributeLine.create(
            {
                "product_tmpl_id": cls.product_tmpl_id.id,
                "attribute_id": cls.attr_fuel.id,
                "value_ids": [(6, 0, [cls.value_gasoline.id, cls.value_diesel.id])],
                "required": True,
            }
        )
        cls.attributeLine2 = cls.productAttributeLine.create(
            {
                "product_tmpl_id": cls.product_tmpl_id.id,
                "attribute_id": cls.attr_engine.id,
                "value_ids": [
                    (
                        6,
                        0,
                        [
                            cls.value_218i.id,
                            cls.value_220i.id,
                            cls.value_218d.id,
                            cls.value_220d.id,
                        ],
                    )
                ],
                "required": True,
            }
        )
        cls.configStepLine = cls.productConfigStepLine.create(
            {
                "product_tmpl_id": cls.product_tmpl_id.id,
                "config_step_id": cls.config_step_engine.id,
                "attribute_line_ids": [
                    (6, 0, [cls.attributeLine1.id, cls.attributeLine2.id])
                ],
            }
        )
        cls.config_product = cls.env.ref("product_configurator.bmw_2_series")
        cls.config_product_1 = cls.env.ref(
            "product_configurator.product_config_line_gasoline_engines"
        )
        cls.productConfigSession = cls.env["product.config.session"]
        cls.session_id = cls.productConfigSession.create(
            {
                "product_tmpl_id": cls.config_product.id,
                "value_ids": [
                    (
                        6,
                        0,
                        [
                            cls.value_gasoline.id,
                            cls.value_transmission.id,
                            cls.value_red.id,
                        ],
                    )
                ],
                "user_id": cls.env.user.id,
                "write_date": fields.Datetime.now() - timedelta(days=5),
            }
        )
