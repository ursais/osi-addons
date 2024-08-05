# Import Odoo libs
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleEstimateJobTierValidation(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user_1 = cls.env["res.users"].create(
            {
                "name": "user_project_manager",
                "login": "user_project_manager",
                "groups_id": [
                    (6, 0, [cls.env.ref("project.group_project_manager").id])
                ],
            }
        )

        # Get tier definition model
        cls.tier_def_obj = cls.env["tier.definition"]
        # Get Sale Estimation model
        cls.sale_estimate_job_obj = cls.env["sale.estimate.job"]
        cls.eco_model = cls.env.ref(
            "ol_job_cost_estimator_tier_validation.model_sale_estimate_job"
        )
        # Create tier definition for this test
        cls.tier_def_obj.create(
            {
                "model_id": cls.eco_model.id,
                "review_type": "individual",
                "reviewer_id": cls.test_user_1.id,
                "definition_domain": "[('state', '=', 'draft')]",
            }
        )

    def test01_tier_validation_model_name(self):
        """
        Tests to ensure that the sale.estimate.job model is now part of the options
          on a tier definition.
        """
        self.assertIn(
            "sale.estimate.job", self.tier_def_obj._get_tier_validation_model_names()
        )

    def test02_validation_estimate(self):
        """Testing tier validation process on ECO"""
        # Create an Sale Estimation in the 'draft' stage
        sale_estimate_job = self.env["sale.estimate.job"].create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": self.company_data["default_pricelist"].id,
                "estimate_ids": [
                    Command.create(
                        {
                            "job_type": "material",
                            "product_id": self.company_data["product_order_no"].id,
                            "product_uom_qty": 1,
                            "product_uom": self.company_data[
                                "product_order_no"
                            ].uom_id.id,
                            "price_unit": 1000.0,
                        }
                    )
                ],
            }
        )

        # Request tier validation
        sale_estimate_job.request_validation()

        # Changing to new stage would cause a validation error
        with self.assertRaises(ValidationError):
            sale_estimate_job.estimate_confirm()

        # Validate the tier validation request
        sale_estimate_job.with_user(self.test_user_1).validate_tier()
        self.assertTrue(sale_estimate_job.validated)

        # Change the sale estimation stage to normal
        sale_estimate_job.estimate_confirm()
        # Confirm the stage changed
        self.assertEqual(sale_estimate_job.state, "confirm")
