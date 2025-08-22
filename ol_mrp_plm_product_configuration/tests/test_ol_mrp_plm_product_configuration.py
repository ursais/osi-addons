# Import Odoo libs
from odoo.tests import common, tagged
from odoo.exceptions import UserError

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestEcoStagedConfiguration(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        # ECO type setup: enable staged configuration
        cls.ecotype = cls.env.ref("mrp_plm.ecotype0")
        cls.ecotype.enable_staged_configuration = True

        # Create a product attribute and values
        cls.attribute = cls.env["product.attribute"].create({"name": "Color"})
        cls.value_red = cls.env["product.attribute.value"].create(
            {"name": "Red", "attribute_id": cls.attribute.id}
        )
        cls.value_blue = cls.env["product.attribute.value"].create(
            {"name": "Blue", "attribute_id": cls.attribute.id}
        )

        # Create a product template with one attribute line containing both values
        cls.product = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "list_price": 100,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [
                                (6, 0, [cls.value_red.id, cls.value_blue.id])
                            ],
                        },
                    )
                ],
            }
        )

    def test_show_staged_configuration_compute(self):
        """Test that show_staged_configuration computes correctly from ECO type."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO Test",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )

        # Expect True because ECO type has enable_staged_configuration=True
        self.assertTrue(
            eco.show_staged_configuration, "ECO should show staged configuration"
        )

    def test_action_new_revision_populates_staged_lines(self):
        """Test that action_new_revision snapshots product attribute lines into ECO."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO New Rev",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )
        eco.action_new_revision()

        # After revision, staged_attribute_line_ids should exist
        self.assertTrue(eco.staged_attribute_line_ids, "Staged lines should be created")
        line = eco.staged_attribute_line_ids[0]

        # The staged line should reference the same attribute as the product
        self.assertEqual(line.attribute_id, self.attribute)

        # Default min_qty/max_qty are copied correctly (0 if PTAVs have none)
        self.assertEqual(line.min_qty, 0, "min_qty should default to 0")
        self.assertEqual(line.max_qty, 0, "max_qty should default to 0")

    def test_apply_staged_configuration_updates_product(self):
        """Test that applying staged configuration modifies the product template attributes."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO Apply",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )
        eco.action_new_revision()
        staged = eco.staged_attribute_line_ids[0]

        # Remove "Blue" to test diff computation and application
        staged.write({"value_ids": [(6, 0, [self.value_red.id])]})
        eco.action_apply()

        # Product should now have only "Red" as attribute value
        ptal = self.product.attribute_line_ids.filtered(
            lambda l: l.attribute_id == self.attribute
        )
        self.assertEqual(
            ptal.value_ids, self.value_red, "Product PTAL should only have 'Red' value"
        )

        # ECO chatter message should indicate product configuration update
        self.assertIn(
            "Product configuration updated",
            eco.message_ids[0].body,
            "ECO message should contain update summary",
        )

    def test_apply_staged_configuration_qty_changes(self):
        """Test that staged min_qty/max_qty updates PTAVs when is_qty_required=True."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO Qty Test",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )
        eco.action_new_revision()
        line = eco.staged_attribute_line_ids[0]

        # Enable quantity requirement and set min/max quantities
        line.write({"is_qty_required": True, "min_qty": 5, "max_qty": 10})
        eco.action_apply()

        ptal = self.product.attribute_line_ids.filtered(
            lambda l: l.attribute_id == self.attribute
        )
        ptav = ptal.product_template_value_ids[0]

        # Assert PTAV default_qty and maximum_qty updated correctly
        self.assertEqual(
            ptav.default_qty, 5, "PTAV default_qty should match staged min_qty"
        )
        self.assertEqual(
            ptav.maximum_qty, 10, "PTAV maximum_qty should match staged max_qty"
        )

    def test_attribute_line_default_val_behavior(self):
        """Test auto-setting default_val when required=True and only one value left."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO Default Val",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )
        eco.action_new_revision()
        line = eco.staged_attribute_line_ids[0]

        # Only one value left and required=True triggers auto default
        line.write({"required": True, "value_ids": [(6, 0, [self.value_red.id])]})

        # Assert that default_val was automatically set to the remaining value
        self.assertEqual(
            line.default_val,
            self.value_red,
            "default_val should be auto-set to remaining value when required=True",
        )

    def test_bom_write_blocking_under_open_eco(self):
        """Test that writing protected fields on BoM is blocked if open ECO controls it."""
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product.id,
                "product_qty": 1,
                "type": "normal",
                "active": False,  # inactive, ECO-controlled
            }
        )
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO BoM",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
                "rebuild_scaffold_bom": True,
            }
        )
        eco.write({"stage_id": self.env.ref("mrp_plm.ecostage_progress").id})
        eco.new_bom_id = bom

        # Attempting to modify a protected field (product_qty) should raise UserError
        with self.assertRaises(UserError):
            bom.write({"product_qty": 5})

        # Modifying safe fields like sequence should succeed
        bom.write({"sequence": 99})
        self.assertEqual(
            bom.sequence,
            99,
            "Safe fields should still be writable even under ECO control",
        )

    def test_compute_diff_and_render_html(self):
        """Test internal diff computation and HTML rendering for staged vs product attributes."""
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO Diff Test",
                "type_id": self.ecotype.id,
                "type": "product",
                "product_tmpl_id": self.product.id,
            }
        )
        eco.action_new_revision()
        line = eco.staged_attribute_line_ids[0]

        # Modify staged line to simulate changes (triggers updates)
        line.write({"value_ids": [(6, 0, [self.value_red.id])]})

        # Compute diff between product and staged lines
        diff = eco._compute_configuration_diff(
            self.product, eco.staged_attribute_line_ids
        )

        # Assert that diff contains either updates, adds, or removes
        self.assertTrue(
            diff["updates"] or diff["adds"] or diff["removes"],
            "Diff should detect changes between product and staged lines",
        )

        # Render HTML summary and ensure it contains attribute name and sections
        html = eco._render_change_summary_html(diff)
        self.assertIn(
            "Attributes", html, "Rendered HTML should include 'Attributes' heading"
        )
        self.assertIn(
            self.attribute.name, html, "Rendered HTML should include attribute name"
        )
