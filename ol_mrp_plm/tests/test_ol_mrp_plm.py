# Import Odoo libs
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestPLMProductState(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        # Get eco stage and product stage from demo data
        cls.ecostage_new = cls.env.ref("mrp_plm.ecostage_new")
        cls.product_state_draft = cls.env.ref("product_state.product_state_draft")

        # Configure the product draft stage on the eco new stage
        cls.ecostage_new.write({"product_state_id": cls.product_state_draft.id})

        # Get the eco in progress stage, sellable product state from demo data
        cls.ecostage_progress = cls.env.ref("mrp_plm.ecostage_progress")
        cls.product_state_sellable = cls.env.ref("product_state.product_state_sellable")

        # Configure the product sellable stage on the eco in progross stage
        # Also allow bom edits
        cls.ecostage_progress.write(
            {
                "product_state_id": cls.product_state_sellable.id,
                "allow_bom_edits": False,
            }
        )

        # Get eco type and normal/admin users from demo data
        cls.ecotype0 = cls.env.ref("mrp_plm.ecotype0")
        cls.test_user_demo = cls.env.ref("base.user_demo")
        cls.test_user_admin = cls.env.ref("base.user_admin")

        # Create a new simple product only needed for this test
        cls.product = cls.env["product.template"].create(
            [
                {
                    "name": "Test product",
                    "list_price": 500,
                }
            ]
        )

        # Create BOM with a few components to use only for this test
        product_to_build = cls.env["product.product"].create(
            {
                "name": "Laptop",
                "type": "product",
                "product_state_id": cls.product_state_draft.id,
            }
        )
        product_to_use_1 = cls.env["product.product"].create(
            {
                "name": "Body",
                "type": "product",
            }
        )
        product_to_use_2 = cls.env["product.product"].create(
            {
                "name": "display",
                "type": "product",
            }
        )
        cls.bom_1 = cls.env["mrp.bom"].create(
            {
                "product_id": product_to_build.id,
                "product_tmpl_id": product_to_build.product_tmpl_id.id,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "product_qty": 3.0,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": product_to_use_2.id, "product_qty": 1}),
                    (0, 0, {"product_id": product_to_use_1.id, "product_qty": 1}),
                ],
            }
        )

    def test_action_new_revision_ol(self):
        """Start a new ECO for product revision"""
        mrp_eco = self.env["mrp.eco"].create(
            [
                {
                    "name": "Test MRP ECO",
                    "type_id": self.ecotype0.id,
                    "type": "product",
                    "product_tmpl_id": self.product.id,
                }
            ]
        )
        mrp_eco.action_new_revision()
        mrp_eco.write({"stage_id": self.ecostage_new.id})
        mrp_eco.write({"stage_id": self.ecostage_progress.id})

    def test_product_allow_modification(self):
        """Test that the invoice_policy field of a product can only be
        modified by an admin user."""
        with self.assertRaises(ValidationError):
            self.product.with_user(self.test_user_demo).write(
                {"invoice_policy": "delivery"}
            )
        self.assertNotEqual(self.product.invoice_policy, "delivery")

        self.product.with_user(self.test_user_admin).write(
            {"invoice_policy": "delivery"}
        )
        self.assertEqual(self.product.invoice_policy, "delivery")

    def test_bom_allow_modification(self):
        """Test that the product_qty field of a product can only be
        modified by an admin user."""
        self.assertEqual(
            self.bom_1.product_id.product_state_id, self.product_state_draft
        )
        with self.assertRaises(ValidationError):
            self.bom_1.with_user(self.test_user_demo).write({"product_qty": 5.0})
        self.assertNotEqual(self.bom_1.product_qty, 5.0)

        self.bom_1.with_user(self.test_user_admin).write({"product_qty": 5.0})
        self.assertEqual(self.bom_1.product_qty, 5.0)

    def test_change_product_stages(self):
        """Test that the product_state_id of a product can be changed by
        writing to the stage_id field of ECO."""
        mrp_eco = self.env["mrp.eco"].create(
            [
                {
                    "name": "Test MRP ECO",
                    "type_id": self.ecotype0.id,
                    "type": "product",
                    "product_tmpl_id": self.product.id,
                    "stage_id": self.ecostage_new.id,
                }
            ]
        )
        self.assertNotEqual(
            self.product.product_state_id, self.ecostage_progress.product_state_id
        )
        mrp_eco.write({"stage_id": self.ecostage_progress.id})
        self.assertEqual(
            self.product.product_state_id, self.ecostage_progress.product_state_id
        )
