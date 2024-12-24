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
        cls.product_obj = cls.env['product.product']
        cls.bom_obj = cls.env['mrp.bom']
        cls.product = cls.company_data["product_order_no"]
        cls.product.sale_delay = 5.0
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_to_use_1 = cls.product_obj.create({
            'name': 'Botox',
            'type': 'product',
            'tracking': "none",
        })
        cls.product_to_use_2 = cls.product_obj.create({
            'name': 'Old Tom',
            'type': 'product',
            'tracking': "none",
        })

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

    def test02_sale_estimate_add_components(self):
        sale_estimate_job = self.sale_estimate_job_obj.create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": self.company_data["default_pricelist"].id,
            }
        )

        young_tom_product = self.env['product.template'].create({
            'name': 'Young Tom',
            'tracking': "none",
            'type': 'product',
            'bom_ids': [Command.create({
                'product_qty': 2.0,
                'bom_line_ids': [
                    Command.create({'product_id': self.product_to_use_1.id, 'product_qty': 2.0}),
                    Command.create({'product_id': self.product_to_use_2.id, 'product_qty': 2.0})
                ],
            })],
        })

        self.assertFalse(sale_estimate_job.estimate_ids.ids)
        self.env['add.components.wizard'].with_context(active_id=sale_estimate_job.id).create({
            "product_id": young_tom_product.product_variant_id.id
        }).action_add_components()
        self.assertTrue(sale_estimate_job.estimate_ids.ids)
