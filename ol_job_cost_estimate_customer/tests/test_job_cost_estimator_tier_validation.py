# Import Odoo libs
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleEstimateJobCustomer(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get Sale Estimation model
        cls.sale_estimate_job_obj = cls.env["sale.estimate.job"]
        cls.product = cls.company_data["product_order_no"]
        cls.product.sale_delay = 5.0

    def test01_sale_estimate(self):
        """Testing sale estimate Customer process"""
        # Create an Sale Estimation in the 'draft' stage
        sale_estimate_job = self.sale_estimate_job_obj.create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": self.company_data["default_pricelist"].id,
                "estimate_ids": [
                    Command.create(
                        {
                            "job_type": "material",
                            "product_id": self.product.id,
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

        # Verify that the customer lead time is equal to the product's sale delay
        self.assertEqual(
            sale_estimate_job.estimate_ids.customer_lead,
            self.product.sale_delay
        )
