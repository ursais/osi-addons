from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestSaleOrderInspectionWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env["sale.order"]
        self.Inspection = self.env["sale.order.inspection"]
        self.Wizard = self.env["sale.order.inspection.wizard"]
        self.group_1 = self.env.ref("base.group_user")  # Using existing group

        # Create a sample sale order
        self.sale_order = self.SaleOrder.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
            }
        )

        # Create inspection records
        self.inspection_1 = self.Inspection.create(
            {
                "name": "Inspection A",
                "group_ids": [(6, 0, [self.group_1.id])],
            }
        )
        self.inspection_2 = self.Inspection.create(
            {
                "name": "Inspection B",
                "group_ids": [(6, 0, [])],  # Public
            }
        )

        self.sale_order.order_inspection_ids = [
            (6, 0, (self.inspection_1.id, self.inspection_2.id))
        ]

    def test_default_get(self):
        """Wizard should populate order and inspections by default"""
        wizard = self.Wizard.with_context(active_id=self.sale_order.id).create(
            {"reason": "default"}
        )
        self.assertEqual(wizard.order_id, self.sale_order)
        self.assertIn(self.inspection_1, wizard.order_inspection_ids)
        self.assertIn(self.inspection_2, wizard.order_inspection_ids)

    def test_confirm_all_allowed(self):
        """Confirm should work when user has access to all inspections"""
        wizard = self.Wizard.with_context(active_id=self.sale_order.id).create(
            {
                "reason": "Cleared checks",
                "order_inspection_ids": [(6, 0, [self.inspection_2.id])],
            }
        )
        wizard.confirm()
        self.assertEqual(self.sale_order.order_inspection_ids, self.inspection_2)

    def test_confirm_blocked_removal(self):
        """User shouldn't be able to remove inspection with restricted group"""  # Create a restricted group not assigned to the user
        restricted_group = self.env["res.groups"].create(
            {
                "name": "Restricted Inspection Group",
                "category_id": self.env.ref("base.module_category_sales_management").id,
            }
        )

        # Create an inspection only accessible by the restricted group
        restricted_inspection = self.Inspection.create(
            {
                "name": "Restricted Inspection",
                "group_ids": [(6, 0, [restricted_group.id])],
            }
        )

        # Assign both inspections to the order
        self.sale_order.order_inspection_ids = [
            (6, 0, (restricted_inspection.id, self.inspection_2.id))
        ]

        # Simulate wizard where user tries to remove the restricted one
        wizard = self.Wizard.with_context(active_id=self.sale_order.id).create(
            {
                "reason": "Trying to remove restricted inspection",
                "order_inspection_ids": [
                    (6, 0, [self.inspection_2.id])
                ],  # Only keeping public one
            }
        )

        with self.assertRaises(
            UserError
        ), self.cr.savepoint():  # Avoid rolling back other test data
            wizard.confirm()
