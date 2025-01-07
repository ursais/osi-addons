from odoo.tests import common, tagged
from odoo import exceptions


@tagged("-at_install", "post_install")
class TestCRMLead(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
    
        cls.CRMLead = cls.env["crm.lead"]
        cls.PurchaseRequest = cls.env["purchase.request"]

        # Create a test lead
        cls.lead = cls.CRMLead.create({"name": "Test Lead"})

        # Create purchase requests linked to the lead
        cls.purchase_request1 = cls.PurchaseRequest.create(
            {"name": "Test Purchase Request 1", "opportunity_id": cls.lead.id}
        )
        cls.purchase_request2 = cls.PurchaseRequest.create(
            {"name": "Test Purchase Request 2", "opportunity_id": cls.lead.id}
        )

        cls.lead2 = cls.CRMLead.create({"name": "Test Lead 2"})

    def test_compute_purchase_request_count(self):
        """Test the computation of purchase_request_count."""
        self.lead._compute_purchase_request_count()
        self.assertEqual(
            self.lead.purchase_request_count,
            2,
            "Purchase request count should be 2",
        )

    def test_action_view_purchase_request(self):
        """Test the action_view_purchase_request method."""
        action = self.lead.action_view_purchase_request()

        # Check if the returned action is correct
        self.assertIn("type", action)
        self.assertEqual(action["type"], "ir.actions.act_window")

        # Check if the domain is set correctly when multiple purchase requests exist
        self.assertIn("domain", action)
        self.assertIn(("id", "in", self.lead.purchase_request_ids.ids), action["domain"])

        # Simulate a single purchase request scenario
        single_request = self.PurchaseRequest.create(
            {"name": "Single Purchase Request", "opportunity_id": self.lead2.id}
        )
        self.lead2._compute_purchase_request_count()
        action_single = self.lead2.action_view_purchase_request()

        self.assertEqual(
            action_single.get("res_id"),
            single_request.id,
            "The res_id should point to the single purchase request's ID.",
        )
