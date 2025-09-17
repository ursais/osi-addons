from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class WorkorderUnitTests(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create companies
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

        # Create product and variant
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        cls.product_variant = cls.product_tmpl.product_variant_id

        # Create BOM for the template
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_tmpl.id,
                "product_id": cls.product_variant.id,
                "type": "normal",
                "company_id": False,
            }
        )

        # Create routing with two workcenters: Build and Test
        cls.workcenter_build = cls.env["mrp.workcenter"].create(
            {
                "name": "Build Center",
                "company_id": False,
            }
        )
        cls.workcenter_test = cls.env["mrp.workcenter"].create(
            {
                "name": "Test Center",
                "company_id": False,
            }
        )

        # Operations associated with bom A
        cls.routing_build_bom = cls.env["mrp.routing.workcenter"].create(
            {
                "name": "Build",
                "workcenter_id": cls.workcenter_build.id,
                "sequence": 1,
                "bom_id": cls.bom.id,
            }
        )
        cls.routing_test_bom = cls.env["mrp.routing.workcenter"].create(
            {
                "name": "Test",
                "workcenter_id": cls.workcenter_test.id,
                "sequence": 2,
                "bom_id": cls.bom.id,
            }
        )

    def test_time_cycle_manual(self):
        """
        Test that company dependecy works with operations on the BOM
        """
        self.routing_build_bom.with_company(self.company_a).write(
            {"time_cycle_manual": 10}
        )
        self.routing_build_bom.with_company(self.company_b).write(
            {"time_cycle_manual": 12}
        )
        self.routing_test_bom.with_company(self.company_a).write(
            {"time_cycle_manual": 20}
        )
        self.routing_test_bom.with_company(self.company_b).write(
            {"time_cycle_manual": 25}
        )

        self.assertEqual(
            self.routing_build_bom.with_company(self.company_a).time_cycle_manual,
            10,
            "Manual Cycle Time in Company A is not correct!",
        )
        self.assertEqual(
            self.routing_build_bom.with_company(self.company_b).time_cycle_manual,
            12,
            "Manual Cycle Time in Company B is not correct!",
        )
        self.assertEqual(
            self.routing_test_bom.with_company(self.company_a).time_cycle_manual,
            20,
            "Manual Cycle Time in Company A is not correct!",
        )
        self.assertEqual(
            self.routing_test_bom.with_company(self.company_b).time_cycle_manual,
            25,
            "Manual Cycle Time in Company B is not correct!",
        )

        self.routing_build_bom.with_company(self.company_a).write(
            {"time_cycle_manual": 11}
        )
        self.assertEqual(
            self.routing_build_bom.with_company(self.company_a).time_cycle_manual,
            11,
            "Manual Cycle Time in Company A is not correct after update!",
        )
        self.assertEqual(
            self.routing_build_bom.with_company(self.company_b).time_cycle_manual,
            12,
            "Manual Cycle Time in Company B should not update after update in company A!",
        )

    def test_batch_duration_computation(self):
        """
        Ensure that the operations on MOs are properly resulting in expected durations
        on Batch objects
        """
        # Set manual cycle times for Bom A's operations in company A
        self.routing_build_bom.with_company(self.company_a).write(
            {"time_cycle_manual": 10}
        )
        self.routing_test_bom.with_company(self.company_a).write(
            {"time_cycle_manual": 20}
        )

        mo_a = (
            self.env["mrp.production"]
            .with_company(self.company_a)
            .create(
                {
                    "product_id": self.product_variant.id,
                    "product_qty": 1.0,
                    "product_uom_id": self.product_variant.uom_id.id,
                    "bom_id": self.bom.id,
                }
            )
        )
        mo_b = (
            self.env["mrp.production"]
            .with_company(self.company_a)
            .create(
                {
                    "product_id": self.product_variant.id,
                    "product_qty": 1.0,
                    "product_uom_id": self.product_variant.uom_id.id,
                    "bom_id": self.bom.id,
                }
            )
        )

        # Trigger generation of moves / workorders
        mo_a.action_confirm()
        mo_b.action_confirm()
        self.assertTrue(
            mo_a.workorder_ids, "Workorders were not generated from BOM operations."
        )
        self.assertTrue(
            mo_b.workorder_ids, "Workorders were not generated from BOM operations."
        )

        batch_vals = {
            "name": "Test Batch",
            "company_id": self.company_a.id,
            "responsible_id": self.env.user.id,
        }
        batch_a = self.env["mrp.production.batch"].create(batch_vals)

        mo_a.write({"mrp_batch_id": batch_a.id})
        mo_b.write({"mrp_batch_id": batch_a.id})

        self.assertTrue(mo_a.mrp_batch_id, "MO A not linked to Batch.")
        self.assertTrue(mo_b.mrp_batch_id, "MO B not linked to Batch.")

        self.assertEqual(
            batch_a.avg_duration_expected,
            30,
            "Average Duration Expected is not correct!",
        )
        self.assertEqual(
            batch_a.total_duration_expected,
            60,
            "Total Duration Expected is not correct!",
        )

        # Set manual cycle times for Bom A's operations in company B
        self.routing_build_bom.with_company(self.company_b).write(
            {"time_cycle_manual": 15}
        )
        self.routing_test_bom.with_company(self.company_b).write(
            {"time_cycle_manual": 25}
        )

        self.assertEqual(
            batch_a.avg_duration_expected,
            30,
            "Total Duration Expected is not correct in company A after time cycle edited in company B!",
        )
        self.assertEqual(
            batch_a.total_duration_expected,
            60,
            "Total Duration Expected is not correct in company A after time cycle edited in company B!",
        )

        # Create MOs in company B
        mo_c = (
            self.env["mrp.production"]
            .with_company(self.company_b)
            .create(
                {
                    "product_id": self.product_variant.id,
                    "product_qty": 1.0,
                    "product_uom_id": self.product_variant.uom_id.id,
                    "bom_id": self.bom.id,
                }
            )
        )
        mo_d = (
            self.env["mrp.production"]
            .with_company(self.company_b)
            .create(
                {
                    "product_id": self.product_variant.id,
                    "product_qty": 1.0,
                    "product_uom_id": self.product_variant.uom_id.id,
                    "bom_id": self.bom.id,
                }
            )
        )

        # Trigger generation of moves / workorders
        mo_c.action_confirm()
        mo_d.action_confirm()
        self.assertTrue(
            mo_c.workorder_ids, "Workorders were not generated from BOM operations."
        )
        self.assertTrue(
            mo_d.workorder_ids, "Workorders were not generated from BOM operations."
        )

        batch_vals = {
            "name": "Test Batch",
            "company_id": self.company_b.id,
            "responsible_id": self.env.user.id,
        }
        batch_b = self.env["mrp.production.batch"].create(batch_vals)

        mo_c.write({"mrp_batch_id": batch_b.id})
        mo_d.write({"mrp_batch_id": batch_b.id})

        self.assertTrue(mo_c.mrp_batch_id, "MO C not linked to Batch.")
        self.assertTrue(mo_d.mrp_batch_id, "MO D not linked to Batch.")

        self.assertEqual(
            batch_b.avg_duration_expected,
            40,
            "Average Duration Expected is not correct!",
        )
        self.assertEqual(
            batch_b.total_duration_expected,
            80,
            "Total Duration Expected is not correct!",
        )
