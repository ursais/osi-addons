# Copyright 2024 Open Source Integrators Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestPurchaseAnalyticRequired(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref("analytic.group_analytic_accounting")
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.product = cls.env.ref("product.product_product_9")
        
        # Create analytic plan and account
        analytic_plan = cls.env["account.analytic.plan"].create({"name": "Test Plan"})
        cls.analytic_account = cls.env["account.analytic.account"].create({
            "name": "Test Analytic Account",
            "plan_id": analytic_plan.id
        })
        cls.analytic_distribution = {str(cls.analytic_account.id): 100}
        
        # Create expense account with analytic policy 'always'
        cls.expense_account = cls.env["account.account"].create({
            "name": "Test Expense Account",
            "code": "TEST_EXP",
            "account_type": "expense",
            "analytic_policy": "always",
        })
        
        # Update product to use the test expense account
        cls.product.property_account_expense_categ_id = cls.expense_account

    def test_purchase_order_analytic_required_validation(self):
        """Test that purchase order validation fails without analytic distribution."""
        po = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
        })
        
        # Add a line without analytic distribution
        self.env["purchase.order_line"].create({
            "order_id": po.id,
            "product_id": self.product.id,
            "product_qty": 1,
            "price_unit": 100,
        })
        
        # Should raise ValidationError when trying to confirm
        with self.assertRaises(ValidationError) as context:
            po.button_confirm()
        
        self.assertIn("Analytic distribution is required", str(context.exception))

    def test_purchase_order_analytic_required_success(self):
        """Test that purchase order validation succeeds with analytic distribution."""
        po = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
            "analytic_distribution": self.analytic_distribution,
        })
        
        # Add a line
        self.env["purchase.order_line"].create({
            "order_id": po.id,
            "product_id": self.product.id,
            "product_qty": 1,
            "price_unit": 100,
        })
        
        # Should succeed
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_purchase_order_line_analytic_required_validation(self):
        """Test that purchase order line validation fails without analytic distribution."""
        po = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
        })
        
        # Should raise ValidationError when creating line without analytic distribution
        with self.assertRaises(ValidationError) as context:
            self.env["purchase.order_line"].create({
                "order_id": po.id,
                "product_id": self.product.id,
                "product_qty": 1,
                "price_unit": 100,
            })
        
        self.assertIn("Analytic distribution is required", str(context.exception))

    def test_purchase_order_line_analytic_required_success(self):
        """Test that purchase order line validation succeeds with analytic distribution."""
        po = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
        })
        
        # Should succeed with analytic distribution
        line = self.env["purchase.order_line"].create({
            "order_id": po.id,
            "product_id": self.product.id,
            "product_qty": 1,
            "price_unit": 100,
            "analytic_distribution": self.analytic_distribution,
        })
        
        self.assertTrue(line.analytic_distribution)

    def test_purchase_order_analytic_never_policy(self):
        """Test that analytic distribution is not allowed when policy is 'never'."""
        # Create account with 'never' policy
        never_account = self.env["account.account"].create({
            "name": "Never Analytic Account",
            "code": "NEVER_ANALYTIC",
            "account_type": "expense",
            "analytic_policy": "never",
        })
        
        # Update product to use the never account
        self.product.property_account_expense_categ_id = never_account
        
        po = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
        })
        
        # Should raise ValidationError when trying to set analytic distribution
        with self.assertRaises(ValidationError) as context:
            self.env["purchase.order_line"].create({
                "order_id": po.id,
                "product_id": self.product.id,
                "product_qty": 1,
                "price_unit": 100,
                "analytic_distribution": self.analytic_distribution,
            })
        
        self.assertIn("Analytic distribution is not allowed", str(context.exception))
