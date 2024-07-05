from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError

@tagged("-at_install", "post_install")
class ConfigurationCreate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attr_ssd = cls.env["product.attribute"].create(
            {
                "name": "SSD",
                "value_ids": [
                    (0, 0, {"name": "SSD-512GB"}),
                    (0, 0, {"name": "SSD-1TB"}),
                ],
            }
        )
        cls.value_ssd256 = cls.env["product.attribute.value"].create({
            "name":"SSD-256GB",
            "attribute_id":cls.attr_ssd.id
        })

        cls.attr_ram = cls.env["product.attribute"].create(
            {
                "name": "RAM",
                "value_ids": [
                    (0, 0, {"name": "RAM-16GB"}),
                    (0, 0, {"name": "RAM-32GB"}),
                ],
            }
        )
        cls.value_ram8gb = cls.env["product.attribute.value"].create({
            "name":"RAM-8GB",
            "attribute_id":cls.attr_ram.id
        })
        cls.test_product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Computer System",
                "config_ok": True,
                "type": "consu",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attr_ssd.id,
                            "value_ids": [
                                (6, 0, cls.attr_ssd.value_ids.ids),
                            ],
                            "required": True,
                            "is_qty_required":True
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attr_ram.id,
                            "value_ids": [
                                (6, 0, cls.attr_ram.value_ids.ids),
                            ],
                            "required": True,
                        },
                    )
                ],
            }
        )

        cls.component_ram = cls.env["product.template"].create({
            "name": "Component-RAM",
            "type": "consu",
            "categ_id": cls.env.ref("product.product_category_all").id,
        })

        cls.component_ssd = cls.env["product.template"].create({
            "name": "Component-SSD",
            "type": "consu",
            "categ_id": cls.env.ref("product.product_category_all").id,
        })
        cls.ssd_config_set = cls.env["mrp.bom.line.configuration.set"].create({
            "name":"SSD-Config Set",
            "configuration_ids":[(0,0,{"value_ids":[(6,0,cls.value_ssd256.ids)]})]
            })

    def test_01_check_default_qty_maximum_qty(self):
        attr_ssd_val = self.env["product.template.attribute.value"].search([("attribute_id","=",self.attr_ssd.id)])
        with self.assertRaises(ValidationError):
            attr_ssd_val.write({
                "default_qty":2,
                "maximum_qty":1
            })
        attr_ssd_val.write({
            "default_qty":1,
            "maximum_qty":5,
        })

    def test_02_create_product_config_wizard(self):
        ProductConfWizard = self.env["product.configurator"]
        product_config_wizard = ProductConfWizard.create(
            {
                "product_tmpl_id": self.test_product_tmpl.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{self.attr_ssd.id}": self.value_ssd256.id,
                f"__qty_{self.attr_ssd.id}": 2,
                f"__attribute_{self.attr_ram.id}": self.value_ram8gb.id,
            }
        )
        product_config_wizard.action_next_step()

    def test_03_create_mrp_order(self):
        MRPBom = self.env["mrp.bom"]
        self.value_ssd256.write({'product_id':self.component_ssd.product_variant_id.id})
        computer_system_bom = MRPBom.create({
            "product_tmpl_id":self.test_product_tmpl.id,
            "config_ok": True,
            "bom_line_ids":[
                (0,0,{"product_id":self.component_ram.product_variant_id.id,"product_tmpl_id":self.component_ram.id,"product_qty":2,"product_uom_id":self.env.ref("uom.product_uom_unit").id,"config_set_id":self.ssd_config_set.id}),
                (0,0,{"product_id":self.component_ssd.product_variant_id.id,"product_tmpl_id":self.component_ssd.id,"product_qty":1,"product_uom_id":self.env.ref("uom.product_uom_unit").id})
            ]
        })
        ProductConfWizard = self.env["product.configurator"]
        product_config_wizard = ProductConfWizard.create(
            {
                "product_tmpl_id": self.test_product_tmpl.id,
            }
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write(
            {
                f"__attribute_{self.attr_ssd.id}": self.value_ssd256.id,
                f"__qty_{self.attr_ssd.id}": 2,
                f"__attribute_{self.attr_ram.id}": self.value_ram8gb.id,
            }
        )
        product_config_wizard.action_next_step()
