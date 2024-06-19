# Import Odoo libs
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestProductTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_ids = cls.env.ref("base.group_system").ids
        cls.test_user_1 = cls.env["res.users"].create(
            {
                "name": "John",
                "login": "test1",
                "groups_id": [(6, 0, group_ids)],
                "email": "test@examlple.com",
            }
        )

        cls.tier_def_obj = cls.env["tier.definition"]
        cls.eco_type = cls.env.ref("mrp_plm.ecotype0")
        cls.product = cls.env.ref(
            "mrp.product_product_computer_desk_bolt_product_template"
        )
        cls.draft_stage = cls.env.ref("mrp_plm.ecostage_new").write(
            {"state": "progress"}
        )
        cls.normal_stage = cls.env.ref("mrp_plm.ecostage_progress").write(
            {"state": "approved"}
        )

    def test_tier_validation_model_name(self):
        self.assertIn("mrp.eco", self.tier_def_obj._get_tier_validation_model_names())

    def test_validation_eco(self):
        eco = self.env["mrp.eco"].create(
            {
                "name": "ECO for test",
                "type_id": self.eco_type.id,
                "type": "product",
                "product_id": self.product.id,
                "stage_id": self.draft_state.id,
            }
        )
        eco.request_validation()
        eco.with_user(self.test_user_1).validate_tier()
        eco.write({"stage_id": self.normal_stage.id})
        self.assertEqual(eco.state, self.normal_stage.state)
