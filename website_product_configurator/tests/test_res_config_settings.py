from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResConfigObj = cls.env["res.config.settings"]
        cls.res_config = cls.ResConfigObj.create(
            {
                "website_tmpl_id": cls.env.ref(
                    "website_product_configurator.config_form_base"
                ).id,
            }
        )
        cls.res_config_select = cls.ResConfigObj.create(
            {
                "website_tmpl_id": cls.env.ref(
                    "website_product_configurator.config_form_select"
                ).id,
            }
        )
        cls.res_config_select.set_values()

    def test_res_config_settings(self):
        self.assertTrue(self.res_config)
        self.assertEqual(
            self.res_config.website_tmpl_id,
            self.env.ref("website_product_configurator.config_form_base"),
        )
        self.assertTrue(self.res_config_select)
        self.assertEqual(
            self.res_config_select.website_tmpl_id,
            self.env.ref("website_product_configurator.config_form_select"),
        )
