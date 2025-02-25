from odoo.tests import common, tagged
from odoo import exceptions

from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestSaleOrder(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.SaleOrder = cls.env["sale.order"]
        cls.CRMLead = cls.env["crm.lead"]
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
        cls.crm_stage2 = cls.env["crm.stage"].create(
            {
                "name": "Qualified",
                "team_id": cls.team.id,
                "tag_ids": [(6, 0, cls.crm_tags.ids)],
            }
        )

    def test_sale_order_with_crm_stage_tags(self):
        lead = self.CRMLead.create(
            {
                "name": "Test Lead",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "team_id": self.team.id,
                "stage_id": self.crm_stage1.id,
            }
        )
        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "opportunity_id": lead.id,
            }
        )
        self.assertEqual(len(self.crm_stage1.tag_ids), len(sale_order.tag_ids))

    def test_onchange_opportunity_id(self):
        lead1 = self.CRMLead.create(
            {
                "name": "Test Lead 1",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "team_id": self.team.id,
                "stage_id": self.crm_stage1.id,
            }
        )
        lead2 = self.CRMLead.create(
            {
                "name": "Test Lead 2",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "team_id": self.team.id,
                "stage_id": self.crm_stage2.id,
            }
        )
        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "opportunity_id": lead1.id,
            }
        )
        sale_order.opportunity_id = lead2
        sale_order._onchange_opportunity_id()
        self.assertFalse(
            any(tag in sale_order.tag_ids for tag in self.crm_stage1.tag_ids)
        )
        self.assertEqual(len(self.crm_stage2.tag_ids), len(sale_order.tag_ids))

    def test_sale_order_without_opportunity(self):
        sale_order = self.SaleOrder.create({"partner_id": self.partner.id})

        # No tags should be assigned
        self.assertFalse(sale_order.tag_ids)
