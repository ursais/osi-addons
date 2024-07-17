# Import Odoo libs
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestSaleTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.ecostage_new = cls.env.ref("mrp_plm.ecostage_new")
        product_state_draft = cls.env.ref("product_state.product_state_draft")
        cls.ecostage_new.write({"product_state_id": product_state_draft.id})

        cls.ecostage_progress = cls.env.ref("mrp_plm.ecostage_progress")
        product_state_sellable = cls.env.ref("product_state.product_state_sellable")
        cls.ecostage_progress.write({"product_state_id": product_state_sellable.id})

        cls.ecotype0 = cls.env.ref("mrp_plm.ecotype0")
        cls.product = cls.env["product.template"].create(
            [
                {
                    "name": "Test product",
                    "list_price": 500,
                }
            ]
        )

    def test_cancel_action(self):
        # Create new ECO
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

        # Start revision and move to inprogress stage
        mrp_eco.action_new_revision()
        mrp_eco.write({"stage_id": self.ecostage_progress.id})

        # Call action_cancel method
        # This should raise ValidationError because no cancel stage is set
        with self.assertRaises(ValidationError):
            mrp_eco.action_cancel()

        # Create cancel eco stage
        stage_cancel = self.env["mrp.eco.stage"].create(
            [
                {
                    "name": "Cancel",
                    "cancel_stage": True,
                    "type_ids": [(6, 0, self.ecotype0.id)],
                }
            ]
        )

        # Call action_cancel method
        # This should set the stage to the cancel stage and reset product state
        mrp_eco.action_cancel()

        # Assert that stage_id is updated correctly
        self.assertEqual(mrp_eco.stage_id, stage_cancel.id)

        # Assert that product state is reset to initial state
        self.assertEqual(
            mrp_eco.product_tmpl_id.product_state_id.id,
            mrp_eco.initial_product_state_id.id,
        )

        # Test stage moves outside of button method
        # Move back to inprogress stage
        mrp_eco.write({"stage_id": self.ecostage_progress.id})

        # Set stage_id to the cancel stage
        mrp_eco.write({"stage_id": stage_cancel.id})

        # Assert that product state is reset to initial state
        self.assertEqual(
            mrp_eco.product_tmpl_id.product_state_id.id,
            mrp_eco.initial_product_state_id.id,
        )
