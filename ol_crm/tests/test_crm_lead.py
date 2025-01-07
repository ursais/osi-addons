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
        cls.team = cls.env["crm.team"].create({"name": "Test Team"})
        cls.company = cls.env.company

        cls.lead = cls.CRMLead.create(
            {
                "name": "Test Lead",
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
                "team_id": cls.team.id,
            }
        )
        cls.partner.write(
            {
                "property_product_pricelist": cls.pricelist.id,
                "property_payment_term_id": cls.payment_term.id,
            }
        )

    def test_action_create_estimate(self):
        # Test creation of an estimate
        self.lead.action_create_estimate()
        estimates = self.Estimate.search([("opportunity_id", "=", self.lead.id)])
        self.assertEqual(len(estimates), 1, "Estimate was not created correctly")
        self.assertEqual(estimates.partner_id, self.partner, "Partner mismatch")
        self.assertEqual(estimates.pricelist_id, self.pricelist, "Pricelist mismatch")
        self.assertEqual(estimates.company_id, self.company, "Company mismatch")

    def test_compute_estimate_count(self):
        # Test computation of estimate count
        self.lead.action_create_estimate()
        self.assertEqual(self.lead.estimate_count, 1, "Estimate count incorrect")

    def test_action_view_estimate(self):
        # Test viewing a single estimate
        estimate = self.Estimate.create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "company_id": self.company.id,
                "opportunity_id": self.lead.id,
            }
        )
        action = self.lead.action_view_estimate()
        self.assertEqual(action["res_model"], "sale.estimate.job", "Wrong model in action")
        self.assertEqual(action["res_id"], estimate.id, "Wrong estimate opened")

        # Test viewing multiple estimates
        self.Estimate.create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "company_id": self.company.id,
                "opportunity_id": self.lead.id,
            }
        )
        action = self.lead.action_view_estimate()
        self.assertIn("domain", action, "Domain missing for multiple estimates")
        self.assertEqual(
            action["domain"],
            [("id", "in", self.lead.estimate_ids.ids)],
            "Incorrect domain for multiple estimates",
        )


