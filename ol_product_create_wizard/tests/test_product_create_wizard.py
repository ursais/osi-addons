from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestProductCreateWizard(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test company
        cls.company_1 = cls.env["res.company"].create({"name": "Test Company 1"})

        # Create attributes and values
        cls.attribute = cls.env["product.attribute"].create({"name": "Color"})
        cls.attribute_value = cls.env["product.attribute.value"].create(
            {"name": "Red", "attribute_id": cls.attribute.id}
        )

        # Create ECO type and stage
        cls.eco_type = cls.env["mrp.eco.type"].create({"name": "Test ECO Type"})
        cls.eco_stage = cls.env["mrp.eco.stage"].create(
            {
                "name": "Initial",
                "type_ids": [(6, 0, [cls.eco_type.id])],
                "sequence": 1,
            }
        )

        # Create a product template with attribute lines
        cls.product_template = cls.env["product.template"].create(
            {
                "name": "Original Product",
                "default_code": "ORIG123",
                "config_ok": True,
                "public_destination": "b2c",
                "allow_backorder": True,
                "system_tier": "customer",
                "company_ids_display": [(6, 0, [cls.company_1.id])],
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [(6, 0, [cls.attribute_value.id])],
                            "used_in_sale_description": True,
                            "is_qty_required": True,
                            "default_val": cls.attribute_value.id,
                            "required": True,
                            "multi": True,
                            "custom": False,
                        },
                    ),
                ],
            }
        )

    def test_product_creation_wizard_flow(self):
        """Test full flow of the product creation wizard."""

        # Create the wizard instance with context
        wizard = (
            self.env["product.create.wizard"]
            .with_context(default_product_tmpl_id=self.product_template.id)
            .create(
                {
                    "product_tmpl_id": self.product_template.id,
                    "product_name": "Cloned Product",
                    "prefix": "CLONE",
                    "eco_type_id": self.eco_type.id,
                    "public_destination": "b2b_b2c",
                    "allow_backorder": False,
                    "system_tier": "normal",
                    "company_ids_display": [(6, 0, [self.company_1.id])],
                }
            )
        )

        # Manually copy attribute line to simulate user editing
        wizard.write(
            {
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.attribute.id,
                            "value_ids": [(6, 0, [self.attribute_value.id])],
                            "default_val": self.attribute_value.id,
                            "is_qty_required": True,
                            "multi": True,
                            "custom": False,
                            "required": True,
                            "used_in_sale_description": True,
                        },
                    )
                ],
            }
        )

        # Trigger confirm
        action = wizard.action_confirm()

        # Follow redirection and verify
        self.assertEqual(action["type"], "ir.actions.act_window")
        if action["res_model"] == "product.template":
            product = self.env["product.template"].browse(action["res_id"])
            self.assertEqual(product.name, "Cloned Product")
            self.assertEqual(product.default_code, "CLONE-ORIG123")
            self.assertEqual(product.system_tier, "normal")
            self.assertEqual(product.allow_backorder, False)
            self.assertEqual(product.public_destination, "b2b_b2c")
            self.assertEqual(set(product.company_ids_display.ids), {self.company_1.id})
        elif action["res_model"] == "mrp.eco":
            eco = self.env["mrp.eco"].browse(action["res_id"])
            self.assertEqual(eco.type_id.id, self.eco_type.id)
            self.assertEqual(eco.stage_id.id, self.eco_stage.id)
            self.assertTrue(eco.product_tmpl_id)

    def test_duplicate_internal_reference_raises_error(self):
        """Should raise ValidationError when duplicate default_code is used."""
        self.env["product.template"].create(
            {
                "name": "Existing Product",
                "default_code": "DUPLICATE-ORIG123",
            }
        )

        wizard = self.env["product.create.wizard"].create(
            {
                "product_tmpl_id": self.product_template.id,
                "product_name": "Clone",
                "prefix": "DUPLICATE",  # Will create DUPLICATE-ORIG123
                "eco_type_id": self.eco_type.id,
            }
        )

        with self.assertRaises(ValidationError):
            wizard.action_confirm()
