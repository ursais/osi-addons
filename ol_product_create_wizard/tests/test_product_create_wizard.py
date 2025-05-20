from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestProductCreateWizard(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create basic product template and attribute data for tests
        cls.product_template = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "default_code": "TEST123",
            }
        )
        cls.eco_type = cls.env["mrp.eco.type"].create({"name": "Test ECO Type"})
        cls.attribute = cls.env["product.attribute"].create({"name": "Test Attribute"})
        cls.attribute_value = cls.env["product.attribute.value"].create(
            {
                "name": "Test Attribute Value",
                "attribute_id": cls.attribute.id,
            }
        )

        # Create a wizard and wizard line for reuse in some tests
        cls.wizard = cls.env["product.create.wizard"].create(
            {
                "product_tmpl_id": cls.product_template.id,
                "product_name": "Test Product",
                "prefix": "TEST",
                "eco_type_id": cls.eco_type.id,
            }
        )
        cls.wizard_line = cls.env["product.create.wizard.line"].create(
            {
                "wizard_id": cls.wizard.id,
                "attribute_id": cls.attribute.id,
                "value_ids": [(6, 0, [cls.attribute_value.id])],
                "default_val": cls.attribute_value.id,
                "is_qty_required": True,
                "multi": True,
                "required": True,
                "custom": False,
            }
        )

    def test_default_get(self):
        """Test default_get populates values from product template and set ECO type."""
        wizard = (
            self.env["product.create.wizard"]
            .with_context(default_product_tmpl_id=self.product_template.id)
            .create({})
        )
        self.assertEqual(wizard.product_name, self.product_template.name)
        self.assertEqual(wizard.internal_ref, self.product_template.default_code)
        self.assertEqual(wizard.eco_type_id.name, "New System Enablement")

    def test_onchange_product_tmpl_id(self):
        """Test _onchange_product_tmpl_id sets product-related values correctly."""
        wizard = self.env["product.create.wizard"].create(
            {"product_tmpl_id": self.product_template.id}
        )
        wizard._onchange_product_tmpl_id()
        self.assertEqual(wizard.product_name, self.product_template.name)
        self.assertEqual(wizard.internal_ref, self.product_template.default_code)

    def test_check_duplicate_default_code_raises(self):
        """Test duplicate detect raise ValidationError when a duplicate code exists."""
        # Setup a template with the same default_code that should conflict
        self.env["product.template"].create(
            {
                "name": "Duplicate Product",
                "default_code": "TEST-TEST123",
            }
        )
        wizard = self.env["product.create.wizard"].create(
            {
                "product_tmpl_id": self.product_template.id,
                "prefix": "TEST",
                "internal_ref": "123",
            }
        )
        with self.assertRaises(ValidationError):
            wizard.check_duplicate_default_code("TEST-TEST123")

    def test_check_duplicate_default_code_passes(self):
        """Test no ValidationError is raised when the internal reference is unique."""
        wizard = self.env["product.create.wizard"].create(
            {
                "product_tmpl_id": self.product_template.id,
                "prefix": "UNIQUE",
                "internal_ref": "456",
            }
        )
        # Should pass silently
        wizard.check_duplicate_default_code("UNIQUE-456")

    def test_action_confirm_creates_product_and_eco(self):
        """Test full confirm flow creates a duplicated product and corresponding ECO."""
        wizard = self.env["product.create.wizard"].create(
            {
                "product_tmpl_id": self.product_template.id,
                "product_name": "New Product",
                "prefix": "NEW",
                "eco_type_id": self.eco_type.id,
            }
        )
        result = wizard.action_confirm()

        # Validate that the new product was created with the correct code
        new_product = self.env["product.template"].search(
            [("name", "=", "New Product")], limit=1
        )
        self.assertTrue(new_product)
        self.assertEqual(new_product.default_code, "NEW-TEST123")

        # Validate that an ECO was created and is linked to the new product
        eco = self.env["mrp.eco"].search(
            [("product_tmpl_id", "=", new_product.id)], limit=1
        )
        self.assertTrue(eco)
        self.assertEqual(eco.type_id, self.eco_type)

        # Validate the returned action opens the ECO form view
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "mrp.eco")
        self.assertEqual(result["res_id"], eco.id)

    def test_onchange_value_ids_clears_default(self):
        """Test default_val is cleared when it's no longer in value_ids."""
        self.wizard_line.value_ids = [(6, 0, [])]
        self.wizard_line._onchange_value_ids()
        self.assertFalse(self.wizard_line.default_val)

    def test_onchange_value_ids_keeps_default(self):
        """Test default_val is retained when it remains in value_ids."""
        self.wizard_line.default_val = self.attribute_value
        self.wizard_line.value_ids = [(6, 0, [self.attribute_value.id])]
        self.wizard_line._onchange_value_ids()
        self.assertEqual(self.wizard_line.default_val, self.attribute_value)
