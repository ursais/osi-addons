from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestProductStateOlValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.product_1 = cls.env.ref("ol_product_state.product_template_product_state")

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
        mrp_eco.action_new_revision()
        self.assertEqual(self.product_1.product_state_id.name, "In Development")

        # Move ECO to 'In Progress'
        # Product stage should change to "Normal"
        mrp_eco.stage_id = self.ecostage_progress.id
        self.assertEqual(self.product_1.product_state_id.name, "Normal")

        # Move ECO back to 'New'
        # Product should stay in "Normal" since "In Development" has no stage
        mrp_eco.stage_id = self.env.ref("mrp_plm.ecostage_new").id
        self.assertEqual(self.product_1.product_state_id.name, "Normal")

        # Move ECO to 'Validated'
        # Product stage should change to "Obsolete"
        mrp_eco.stage_id = self.env.ref("mrp_plm.ecostage_validated").id
        mrp_eco.action_apply()
        self.assertEqual(self.product_1.product_state_id.name, "Obsolete")
