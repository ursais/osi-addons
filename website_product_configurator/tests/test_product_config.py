from datetime import timedelta

from odoo import fields

from ..tests.common import (
    TestProductConfiguratorValues,
)


class TestProductConfigStepLine(TestProductConfiguratorValues):
    def test_get_website_template(self):
        self.configStepLine.write(
            {
                "website_tmpl_id": self.env.ref(
                    "website_product_configurator.config_form_radio"
                ).id,
            }
        )
        view_id = self.configStepLine.get_website_template()
        self.assertEqual(
            view_id,
            "website_product_configurator.config_form_radio",
            "We do not return the correct view_id",
        )
        self.configStepLine.write({"website_tmpl_id": False})
        view_id2 = self.configStepLine.get_website_template()
        self.assertEqual(
            view_id2,
            "website_product_configurator.config_form_select",
            "We do not return the correct view_id",
        )

        # set template id false
        self.env["ir.config_parameter"].sudo().set_param(
            "product_configurator.default_configuration_step_website_view_id", False
        )
        dafault_template_xml_id = self.configStepLine.get_website_template()
        self.assertEqual(
            dafault_template_xml_id,
            "website_product_configurator.config_form_select",
            "Default Template xml id is not set.",
        )


class TestProductConfig(TestProductConfiguratorValues):
    def test_remove_inactive_config_sessions(self):
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
                "write_date": fields.Datetime.now() - timedelta(days=5),
            }
        )
        session_id2 = self.productConfigSession.create(
            {
                "product_tmpl_id": self.config_product_1.id,
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
                "write_date": fields.Datetime.now(),
            }
        )

        session_id.remove_inactive_config_sessions()
        sessions_to_remove = self.productConfigSession.search(
            [
                (
                    "id",
                    "=",
                    session_id.id,
                )
            ]
        )
        self.assertFalse(sessions_to_remove, "session_id is not deleted")
        session_id2.remove_inactive_config_sessions()
        sessions_to_remove2 = self.productConfigSession.search(
            [
                (
                    "id",
                    "=",
                    session_id2.id,
                )
            ]
        )
        self.assertTrue(sessions_to_remove2, "session_id does not deleted")
