from odoo.tests import common, tagged
from odoo import exceptions


@tagged("-at_install", "post_install")
class TestCRMLeadBlanketOrder(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test data
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_product_pricelist": cls.env["product.pricelist"]
                .create({"name": "Test Pricelist"})
                .id,
                "property_payment_term_id": cls.env["account.payment.term"]
                .create({"name": "Test Payment Term"})
                .id,
            }
        )
        cls.team = cls.env["crm.team"].create({"name": "Test Sales Team"})
        cls.lead = cls.env["crm.lead"].create(
            {
                "name": "Test Lead",
                "partner_id": cls.partner.id,
                "team_id": cls.team.id,
            }
        )

    def test_action_create_blanket_order(self):
        """Test creating a Blanket Order from a Lead."""
        self.assertEqual(
            len(self.lead.blanket_order_ids),
            0,
            "There should be no Blanket Orders initially.",
        )

        action = self.lead.action_create_blanket_order()
        self.assertEqual(
            action["type"],
            "ir.actions.act_window",
            "The returned action type should be 'ir.actions.act_window'.",
        )
        self.assertEqual(
            action["res_model"],
            "sale.blanket.order",
            "The returned res_model should be 'sale.blanket.order'.",
        )

        # Check that a Blanket Order was created
        self.assertEqual(
            len(self.lead.blanket_order_ids),
            1,
            "A Blanket Order should have been created.",
        )
        blanket_order = self.lead.blanket_order_ids[0]
        self.assertEqual(
            blanket_order.partner_id,
            self.partner,
            "The Blanket Order should reference the correct partner.",
        )
        self.assertEqual(
            blanket_order.opportunity_id,
            self.lead,
            "The Blanket Order should reference the correct Lead.",
        )

    def test_compute_blanket_order_count(self):
        """Test computation of Blanket Order count."""
        self.assertEqual(
            self.lead.blanket_order_count, 0, "Initial Blanket Order count should be 0."
        )
        self.lead.action_create_blanket_order()
        self.lead._compute_blanket_order_count()
        self.assertEqual(
            self.lead.blanket_order_count,
            1,
            "Blanket Order count should be 1 after creating one Blanket Order.",
        )

    def test_action_view_blanket_order(self):
        """Test viewing associated Blanket Orders."""
        # No Blanket Orders case
        action = self.lead.action_view_blanket_order()
        self.assertIn(
            "domain", action, "The action should have a domain for filtering records."
        )
        self.assertEqual(
            action["domain"],
            [("id", "in", [])],
            "The domain should be empty if there are no Blanket Orders.",
        )

        # Single Blanket Order case
        self.lead.action_create_blanket_order()
        action = self.lead.action_view_blanket_order()
        self.assertIn(
            "views",
            action,
            "The action should have a view defined for single Blanket Order.",
        )
        self.assertEqual(
            action["res_id"],
            self.lead.blanket_order_ids[0].id,
            "The res_id should match the single Blanket Order.",
        )

        # Multiple Blanket Orders case
        self.lead.action_create_blanket_order()
        action = self.lead.action_view_blanket_order()
        self.assertIn(
            "domain", action, "The action should have a domain for filtering records."
        )
        self.assertEqual(
            len(action["domain"][0][2]),
            2,
            "The domain should contain both Blanket Orders.",
        )
