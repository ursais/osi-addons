from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestProductStateOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.product_1 = cls.env.ref("ol_base.mc500g_product_template")

        # configure 'New Product Introduction' ECO type stages
        cls.ecostage_progress = cls.env.ref("mrp_plm.ecostage_progress")
        cls.ecostage_effective = cls.env.ref("mrp_plm.ecostage_effective")
        cls.ecostage_progress.product_state_id = cls.env.ref(
            "product_state.product_state_sellable"
        )
        cls.ecostage_effective.product_state_id = cls.env.ref(
            "product_state.product_state_obsolete"
        )

    def test_action_confirm_product_state_changes(self):
        """Test ensures product is able to move product stages correctly with eco stages"""
        # Create new ECO
        mrp_eco = self.env["mrp.eco"].create(
            {
                "name": "Test MRP ECO Stages",
                "type_id": self.env.ref("mrp_plm.ecotype0").id,
                "type": "product",
                "product_tmpl_id": self.product_1.id,
            }
        )
        # First Stage has no product state so product should not change states
        previous_product_stage = self.product_1.product_state_id
        mrp_eco.action_new_revision()
        self.assertEqual(self.product_1.product_state_id, previous_product_stage)

        # Move ECO to 'In Progress'
        # Product stage should change to "Normal" which is set on the "In Progress" ECO Stage
        mrp_eco.stage_id = self.ecostage_progress.id
        self.assertEqual(
            self.product_1.product_state_id, mrp_eco.stage_id.product_state_id
        )

        # Move ECO back to 'New'
        # Product should stay in "Normal" since "In Development" has no stage
        previous_product_stage = self.product_1.product_state_id
        mrp_eco.stage_id = self.env.ref("mrp_plm.ecostage_new").id
        self.assertEqual(self.product_1.product_state_id, previous_product_stage)

        # Move ECO to 'Validated'
        # Product stage should change to "Obsolete" which is set on the "Validated" ECO Stage
        mrp_eco.stage_id = self.env.ref("mrp_plm.ecostage_validated").id
        mrp_eco.action_apply()
        self.assertEqual(
            self.product_1.product_state_id, mrp_eco.stage_id.product_state_id
        )

    def test_check_onchange_category(self):
        """Test changing the product category on the product also changes the candidates."""
        # Create a new category for this test.
        product_category = self.env["product.category"].create(
            {
                "name": "Test category",
                "candidate_sale": True,
                "candidate_purchase": True,
                "candidate_manufacture": True,
            }
        )
        # Create a simple product for testing.
        desk_temp = self.env["product.template"].create(
            {
                "name": "Desk Combination",
            }
        )
        # Verify that the candidate fields are False
        self.assertFalse(desk_temp.categ_id.candidate_sale)
        self.assertFalse(desk_temp.candidate_sale)
        # Change category and trigger onchange
        desk_temp.write({"categ_id": product_category.id})
        desk_temp.onchange_categ_id()
        # Verify that the changes are correct based on category.
        self.assertTrue(desk_temp.candidate_sale)
        self.assertTrue(desk_temp.categ_id.candidate_sale)
        self.assertEqual(desk_temp.candidate_sale, product_category.candidate_sale)
        self.assertEqual(
            desk_temp.candidate_purchase, product_category.candidate_purchase
        )
