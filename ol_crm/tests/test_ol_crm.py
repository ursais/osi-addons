from odoo.tests import common, tagged
from odoo import exceptions

from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestCRMLead(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.CRMLead = cls.env["crm.lead"]
        cls.Estimate = cls.env["sale.estimate.job"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Test Pricelist"})
        cls.payment_term = cls.env["account.payment.term"].create({"name": "Test Term"})
        cls.team = cls.env["crm.team"].create({"name": "CRM Testing Team"})
        cls.company = cls.env.company
        cls.crm_tags = cls.env["crm.tag"].create(
            [{"name": "Unit Test Tag 1"}, {"name": "Unit Test Tag 2"}]
        )
        cls.crm_stage1 = cls.env["crm.stage"].create(
            {
                "name": "New",
                "team_id": cls.team.id,
                "tag_ids": [(6, 0, cls.crm_tags.ids)],
            }
        )

    def test_crm_lead_with_crm_stage_tags(self):
        lead = self.CRMLead.create(
            {
                "name": "Test Lead",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "team_id": self.team.id,
                'stage_id': self.crm_stage1.id
            }
        )
        self.assertEqual(len(self.crm_stage1.tag_ids), len(lead.stage_id.tag_ids))
        self.assertEqual(self.crm_stage1.team_id.id, lead.team_id.id)
