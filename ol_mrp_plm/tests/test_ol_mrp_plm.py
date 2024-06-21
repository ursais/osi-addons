# Copyright 2020 Sergio Teruel <sergio.teruel@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestPLMProductState(common.TransactionCase):
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

    def test_action_new_revision_ol(self):
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
