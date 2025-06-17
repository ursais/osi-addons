from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestComponentReplacement(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eco_type = cls.env["mrp.eco.type"].create(
            {
                "name": "Replace Components ECO Type",
                "component_replacement": True,
            }
        )

        cls.attribute = cls.env["product.attribute"].create({"name": "Color"})
        cls.value_old = cls.env["product.attribute.value"].create(
            {
                "name": "Red",
                "attribute_id": cls.attribute.id,
            }
        )
        cls.value_new = cls.env["product.attribute.value"].create(
            {
                "name": "Blue",
                "attribute_id": cls.attribute.id,
            }
        )

        cls.template_old = cls.env["product.template"].create(
            {
                "name": "Old Component",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, [cls.value_old.id])],
                            "default_val": cls.value_old.id,
                        },
                    )
                ],
            }
        )
        cls.product_old = cls.template_old.product_variant_id

        cls.template_new = cls.env["product.template"].create(
            {
                "name": "New Component",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, [cls.value_new.id])],
                            "default_val": cls.value_new.id,
                        },
                    )
                ],
            }
        )
        cls.product_new = cls.template_new.product_variant_id

        cls.template_main = cls.env["product.template"].create({"name": "Main Product"})
        cls.product_main = cls.template_main.product_variant_id

        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.template_main.id,
                "type": "normal",
                "scaffolding_bom": True,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_old.id,
                            "product_qty": 1.0,
                        },
                    )
                ],
            }
        )

        # Link attribute value to main product
        cls.env["product.template.attribute.line"].create(
            {
                "product_tmpl_id": cls.template_main.id,
                "attribute_id": cls.attribute.id,
                "value_ids": [(6, 0, [cls.value_old.id])],
                "default_val": cls.value_old.id,
            }
        )

        cls.eco = cls.env["mrp.eco"].create(
            {
                "name": "Test Component Replace",
                "type_id": cls.eco_type.id,
                "product_tmpl_id": cls.template_old.id,
                "product_to_add_id": cls.product_new.id,
            }
        )

    def test_onchange_populates_bom_ids(self):
        self.eco._onchange_product_id_bom_ids()
        self.assertIn(
            self.bom, self.eco.bom_ids, "BoM should be auto-populated by onchange"
        )

    def test_action_apply_missing_data(self):
        # Remove new product to simulate incomplete config
        self.eco.product_to_add_id = False
        with self.assertRaises(ValidationError):
            self.eco.action_apply()

    def test_action_apply_valid_replacement(self):
        self.eco._onchange_product_id_bom_ids()
        self.eco.product_to_add_id = self.product_new

        # Should not raise
        self.eco.action_apply()

        line = self.env["product.template.attribute.line"].search(
            [
                ("product_tmpl_id", "=", self.template_main.id),
                ("attribute_id", "=", self.attribute.id),
            ]
        )
        self.assertIn(
            self.value_new, line.value_ids, "New attribute value should be added"
        )
        self.assertNotIn(
            self.value_old, line.value_ids, "Old attribute value should be removed"
        )
        self.assertEqual(
            line.default_val, self.value_new, "Default value should be updated"
        )

    def test_plm_eco_type_flag(self):
        self.assertTrue(
            self.eco_type.component_replacement,
            "Component Replacement flag should be True",
        )
