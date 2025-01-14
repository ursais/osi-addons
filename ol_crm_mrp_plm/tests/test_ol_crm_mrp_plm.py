from odoo.tests import common, tagged
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.fields import Command


@tagged("-at_install", "post_install")
class TestOLCRMPLM(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.Bom = cls.env["mrp.bom"]

        # Set user in the MRP group to access work orders
        grp_workorder = cls.env.ref("mrp.group_mrp_routings")
        cls.env.user.write({"groups_id": [(4, grp_workorder.id)]})

        # Products
        cls.table = cls.env["product.product"].create(
            {
                "name": "Table (MTO)",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.table_sheet = cls.env["product.product"].create(
            {
                "name": "Table Top",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.table_leg = cls.env["product.product"].create(
            {
                "name": "Table Leg",
                "type": "product",
                "tracking": "lot",
            }
        )
        cls.table_bolt = cls.env["product.product"].create(
            {
                "name": "Bolt",
                "type": "product",
            }
        )

        # Workcenters
        cls.workcenter_1 = cls.env["mrp.workcenter"].create(
            {
                "name": "Workcenter",
                "default_capacity": 2,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
            }
        )
        cls.workcenter_2 = cls.env["mrp.workcenter"].create(
            {
                "name": "Nuclear Workcenter",
                "default_capacity": 2,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
            }
        )

        # Bill of Materials (BoM)
        cls.bom_table = cls.Bom.create(
            {
                "product_id": cls.table.id,
                "product_tmpl_id": cls.table.product_tmpl_id.id,
                "product_uom_id": cls.table.uom_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.table_sheet.id, "product_qty": 1}),
                    (0, 0, {"product_id": cls.table_leg.id, "product_qty": 3}),
                ],
                "operation_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "op1",
                            "workcenter_id": cls.workcenter_1.id,
                            "time_cycle_manual": 10,
                            "sequence": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "op2",
                            "workcenter_id": cls.workcenter_2.id,
                            "time_cycle_manual": 10,
                            "sequence": 2,
                        },
                    ),
                ],
            }
        )

        # ECO Type and Stage
        cls.eco_type = cls.env["mrp.eco.type"].search([], limit=1)
        cls.eco_stage = cls.eco_type.stage_ids.filtered("allow_apply_change")[0]

    @classmethod
    def create_crm_lead(cls):
        lead = cls.env["crm.lead"].create({"name": "CRM Lead"})
        return lead

    @classmethod
    def _create_eco(cls, name, bom, type_id, stage_id):
        eco = cls.env["mrp.eco"].create(
            {
                "name": name,
                "bom_id": bom.id,
                "product_tmpl_id": bom.product_tmpl_id.id,
                "type_id": type_id,
                "stage_id": stage_id,
                "type": "bom",
            }
        )
        return eco

    # Test ECO Change
    def test_eco_change(self):
        "Test linking an ECO to a CRM lead and verifying the count."

        # Create an ECO and a CRM Lead
        eco1 = self._create_eco(
            "ECO1", self.bom_table, self.eco_type.id, self.eco_stage.id
        )
        lead = self.create_crm_lead()

        # Link ECO to the Lead
        eco1.opportunity_id = lead.id

        # 🔧 Assertion: Check the linked ECO count
        self.assertEqual(
            lead.eco_count,
            1,
            "ECO count should be 1 after linking the ECO to the lead.",
        )

        # Call the action to view the ECOs
        action = lead.action_view_eco()

        # Assertion: Validate the action return value
        self.assertTrue(
            action, "The action to view ECOs should return a valid action dictionary."
        )
        self.assertIn(
            "type", action, "The action dictionary should contain a 'type' key."
        )

    # Test Sale Estimate
    def test_sale_estimate(self):
        "Test the creation of a sale estimate job and linking it to a CRM opportunity."

        sale_estimate_job_obj = self.env["sale.estimate.job"]
        product = self.env.ref("product.product_product_13")
        product_uom = self.env.ref("uom.product_uom_unit")
        partner = self.env.ref("base.res_partner_1")
        opportunity_id = self.create_crm_lead()

        # Create a Sale Estimate Job
        sale_estimate_job = sale_estimate_job_obj.create(
            {
                "partner_id": partner.id,
                "pricelist_id": partner.property_product_pricelist.id,
                "opportunity_id": opportunity_id.id,
                "estimate_ids": [
                    Command.create(
                        {
                            "job_type": "material",
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": product_uom.id,
                            "price_unit": 1000.0,
                        }
                    )
                ],
            }
        )

        # Assertion: Check the sale estimate job is created successfully
        self.assertTrue(
            sale_estimate_job, "The sale estimate job should be created successfully."
        )

        # Call action_create_eco_and_product and assert no errors
        action = sale_estimate_job.action_create_eco_and_product(
            product.name, self.eco_type
        )
        self.assertTrue(
            action,
            "The action to create an ECO and product should return a valid result.",
        )
