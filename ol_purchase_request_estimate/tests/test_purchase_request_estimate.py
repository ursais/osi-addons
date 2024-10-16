# Import Odoo libs
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestPurchaseRequestEstimate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.sale_estimate_job_obj = self.env["sale.estimate.job"]
        self.purchase_request_obj = self.env["purchase.request"]
        self.wiz_obj = self.env["purchase.request.line.make.purchase.order"]
        self.purchase_request_line_obj = self.env["purchase.request.line"]
        self.product = self.env.ref("product.product_product_13")
        self.product_uom = self.env.ref("uom.product_uom_unit")
        self.partner = self.env.ref("base.res_partner_1")

    def test01_sale_estimate(self):
        # Create an Sale Estimation in the 'draft' stage
        sale_estimate_job = self.sale_estimate_job_obj.create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "estimate_ids": [
                    Command.create(
                        {
                            "job_type": "material",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product_uom.id,
                            "price_unit": 1000.0,
                        }
                    )
                ],
            }
        )
        sale_estimate_job.with_context(
            default_estimate_id=sale_estimate_job.id
        ).action_create_purchase_request()
        purchase_request = sale_estimate_job.purchase_request_ids
        purchase_request_line = purchase_request.line_ids

        # Approve the purchase request
        purchase_request.button_to_approve()
        purchase_request.button_approved()

        # Create a purchase order from the purchase request line
        wiz_id = self.wiz_obj.with_context(
            active_model="purchase.request.line",
            active_ids=purchase_request_line.ids,
            active_id=purchase_request_line.id,
        ).create({"supplier_id": self.env.ref("base.res_partner_12").id})
        wiz_id.make_purchase_order()

        # Verify the purchase order is created correctly
        purchase_order = purchase_request_line.purchase_lines.order_id
        self.assertTrue(
            len(purchase_request_line.purchase_lines), "Should have a purchase line"
        )
        self.assertEqual(
            purchase_request_line.purchase_lines.product_id.id,
            purchase_request_line.product_id.id,
            "Should have same product",
        )

        # Check that purchase order state matches purchase request and estimate line
        self.assertEqual(
            purchase_request_line.purchase_lines.state,
            purchase_request_line.purchase_state,
            "Should have same state in purchase line and purchase request line",
        )

        # Check that the computed 'purchase_state' on estimate line shows RFQ
        self.assertEqual(
            sale_estimate_job.estimate_ids.purchase_state,
            "RFQ",
            "Purchase state on estimate line should match the label 'RFQ'",
        )

        # Approve the purchase order
        purchase_order.button_approve()
        self.assertEqual(
            purchase_order.state,
            sale_estimate_job.estimate_ids.purchase_state,
            "Should have same state on purchase order and estimate line after approval",
        )

        # Check that the computed 'purchase_state' on estimate line shows Purchase Order
        self.assertEqual(
            sale_estimate_job.estimate_ids.purchase_state,
            "To Approve",
            "Purchase state on estimate line should match the label 'To Approve'",
        )
