# Import Odoo libs
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestProductTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set variables from demo data
        cls.test_user_1 = cls.env.ref("base.partner_admin")
        cls.eco_type = cls.env.ref("mrp_plm.ecotype0")
        cls.product = cls.env.ref(
            "mrp.product_product_computer_desk_bolt_product_template"
        )
        # Set states on the stages which tier validation uses
        cls.draft_stage = cls.env.ref("mrp_plm.ecostage_new").write(
            {"state": "progress"}
        )
        cls.normal_stage = cls.env.ref("mrp_plm.ecostage_progress").write(
            {"state": "approved"}
        )

        # Get tier definition model
        cls.tier_def_obj = cls.env["tier.definition"]
        # Get ECO model
        cls.eco_model = cls.env.ref("mrp.model_mrp_eco")
        # Create tier definition for this test
        cls.tier_def_obj.create(
            {
                "model_id": cls.eco_model.id,
                "review_type": "individual",
                "reviewer_id": cls.test_user_1.id,
                "definition_domain": "[('stage_id.name', '=', 'new')]",
            }
        )

    def test_tier_validation_model_name(self):
        """
        Tests to ensure that the mrp.eco model is now part of the options
          on a tier definition.
        """
        self.assertIn("mrp.eco", self.tier_def_obj._get_tier_validation_model_names())

    def test_validation_eco(self):
        """Testing tier validation process on ECO"""
        # Create an ECO in the 'draft' stage
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO for test",
                "type_id": self.eco_type.id,
                "type": "product",
                "product_id": self.product.id,
                "stage_id": self.draft_stage.id,
            }
        )

        # Request tier validation
        eco.request_validation()

        # Changing to new stage would cause a validation error
        with self.assertRaises(ValidationError):
            eco.write({"stage_id": self.normal_stage.id})

        # Validate the tier validation request
        eco.with_user(self.test_user_1).validate_tier()

        # Change the eco stage to normal
        eco.write({"stage_id": self.normal_stage.id})

        # Confirm the stage changed
        self.assertEqual(eco.state, self.normal_stage.state)
