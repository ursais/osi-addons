from odoo.tests import common, tagged
from unittest.mock import MagicMock, patch
import minfraud


@tagged("-at_install", "post_install")
class FraudDetectionTest(common.TransactionCase):
    """
    Test Cases for fraud detection in sale order.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test cases."""
        super().setUpClass()

    def test_get_risk_score_no_check(self):
        """
        Ensure fraud check doesn't run when unnecessary.
        """
        order = self.env["sale.order"].create({})
        self.assertFalse(order.customer_ip)
        order._get_risk_score()
        self.assertFalse(order.check_risk)

        order.customer_ip = "1.1.1.1"
        order._get_risk_score()
        self.assertFalse(order.check_risk)

        bank_transfer_method = self.env["payment.method"].create({"check_risk": False})
        order.payment_method_id = bank_transfer_method
        order._get_risk_score()
        self.assertFalse(order.check_risk)

        self.assertEqual(0.0, order.maxmind_risk_score)
        self.assertFalse(order.maxmind_insights)

    def test_get_risk_score_missing_ip(self):
        """
        Ensure a high risk score is assigned when IP is missing.
        """
        order = self.env["sale.order"].create({"check_risk": True})

        self.assertTrue(order.check_risk)
        self.assertFalse(order.customer_ip)
        self.assertEqual(0.0, order.maxmind_risk_score)
        self.assertFalse(order.maxmind_insights)

        order._get_risk_score()

        self.assertEqual(99, order.maxmind_risk_score)
        self.assertEqual(
            "IP address not found, maxmind score not available.", order.maxmind_insights
        )

    def test_get_risk_score(self):
        """
        Ensure a risk score is set when valid data is provided.
        """
        order = self.env["sale.order"].create({"customer_ip": "1.1.1.1"})
        risky_payment_method = self.env["payment.method"].create({"check_risk": True})
        order.payment_method_id = risky_payment_method

        self.assertRaises(minfraud.MinFraudError, order._get_risk_score)
        self.assertEqual(99, order.maxmind_risk_score)
        self.assertEqual(
            "Could Not Calculate Score: Your account ID or license key could not be authenticated.",
            order.maxmind_insights,
        )

        order.maxmind_risk_score = 0.0
        mock_score = minfraud.models.Score(risk_score=89.03)
        mock_insights = minfraud.models.Insights(
            billing_address=minfraud.models.BillingAddress(distance_to_ip_location=2187)
        )

        with patch("minfraud.Client.score", return_value=mock_score), patch(
            "minfraud.Client.insights", MagicMock(return_value=mock_insights)
        ):
            order._get_risk_score()

        self.assertEqual(89.03, order.maxmind_risk_score)
        self.assertIn(
            "Estimated distance between billing location and IP address",
            order.maxmind_insights,
        )
