from odoo.tests import common, tagged, Form
from datetime import date, timedelta

from odoo import fields, exceptions
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestCreditLimit(common.TransactionCase):
    """
    Test suite for Credit Limit functionality across Sales, Stock,
    Manufacturing, Partners, Blanket Orders, and Deposits.
    """

    @classmethod
    def setUpClass(cls):
        """
        Prepare test environment and commonly used records.
        """
        super().setUpClass()
        # Disable mail notifications to speed up tests
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        # Core models
        cls.blanket_order_obj = cls.env["sale.blanket.order"]

        # References
        cls.customer = cls.env.ref("hr.work_contact_mit")
        cls.product = cls.env.ref("product.product_product_6")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")

        # Pricelist for test sales
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )

    # ==================
    # TEST CASES BELOW #
    # ==================

    def test_check_partner_rollup_id(self):
        """
        Test partner rollup logic:
          - Prevent cyclic rollup references.
          - Validate onchange on credit limit.
        """
        PartnerObj = self.env["res.partner"]

        # Create 2 partners and make them rollup to each other
        rollup_partner_1 = PartnerObj.create({"name": "RollUp Partner A"})
        rollup_partner_2 = PartnerObj.create({"name": "RollUp Partner B"})
        rollup_partner_1.write({"partner_rollup_id": rollup_partner_2.id})

        # Expect UserError due to cyclic reference
        with self.assertRaises(exceptions.UserError):
            rollup_partner_2.write({"partner_rollup_id": rollup_partner_1.id})

        # Trigger onchange for coverage
        partner_2 = PartnerObj.create({"name": "RollUp Partner B", "credit_limit": 0.0})
        partner_2.onchange_credit_limit()

    def test_partner_flow(self):
        """
        Full flow: Partner credit limit → Sale order confirmation →
        Picking validation → Credit hold propagation.
        """
        PartnerObj = self.env["res.partner"]

        # Create parent/child partners with credit rollup
        compnay_a = PartnerObj.create(
            {"name": "Company A", "is_company": True, "credit_limit": 30}
        )
        child_compnay_a = PartnerObj.create(
            {
                "name": "Child A",
                "parent_id": compnay_a.id,
                "partner_rollup_id": compnay_a.id,
            }
        )
        self.assertEqual(compnay_a.remaining_credit, 30)
        self.assertEqual(child_compnay_a.remaining_credit, 30)

        self.customer.credit_limit = 400

        # Create a product and sale order
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 350,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.uom_unit.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        # Confirm sale order
        sale_order.action_confirm()

        # Check balances and credit hold
        self.assertEqual(sale_order.uninvoiced_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.open_so_balance, sale_order.amount_total)
        self.assertFalse(sale_order.partner_id.credit_hold)

        # Remaining credit reduced
        self.assertEqual(
            sale_order.partner_id.remaining_credit,
            sale_order.partner_id.credit_limit - sale_order.amount_total,
        )

        # Picking validation should not be on credit hold
        pick = sale_order.picking_ids
        pick.move_ids.write({"quantity": 1, "picked": True})
        pick.action_assign()
        pick.button_validate()
        self.assertFalse(pick.credit_hold)

    def test_override_credit_limit_hold(self):
        """
        Test that overriding the credit limit hold flag on SO
        prevents credit hold propagation.
        """
        self.customer.credit_limit = 400

        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 400,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "override_credit_limit_hold": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.uom_unit.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        sale_order.action_confirm()

        # Should not be on credit hold even if over the limit
        self.assertFalse(sale_order.partner_id.credit_hold)

        # Picking also bypasses credit hold
        pick = sale_order.picking_ids
        pick.move_ids.write({"quantity": 1, "picked": True})
        pick.button_validate()
        self.assertFalse(pick.credit_hold)

    def test_sale_mrp_flow(self):
        """
        Test Sales → Manufacturing → BOM creation flow under credit limit.
        (Currently partially commented out)
        """
        route_manufacture = self.env.ref("mrp.route_warehouse0_manufacture").id
        route_mto = self.env.ref("purchase_stock.route_warehouse0_buy").id

        partner = self.env["res.partner"].create(
            {"name": "Customer", "credit_limit": 400}
        )

        # Create BOM product and component
        bom_product = self.env["product.product"].create(
            {
                "name": "BOM Prodduct",
                "type": "product",
                "route_ids": [(4, route_mto), (4, route_manufacture)],
                "list_price": 350,
            }
        )
        bom_line = self.env["product.product"].create(
            {"name": "Line Product", "type": "product"}
        )
        self.env["mrp.bom"].create(
            {
                "product_id": bom_product.id,
                "product_tmpl_id": bom_product.product_tmpl_id.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [(0, 0, {"product_id": bom_line.id})],
            }
        )

        # Sale Order creation flow for BOM product is commented out
        # (would normally test that confirming SO triggers MO creation)

    def test_customer_deposit_balance(self):
        """
        Test customer deposit balance updates when payment is created.
        """
        PartnerObj = self.env["res.partner"]
        journal = self.env.ref("account.1_cash")
        partner_1 = PartnerObj.create({"name": "Vandan"})

        # Record a payment
        payment = self.env["account.payment"].create(
            {"partner_id": partner_1.id, "journal_id": journal.id, "amount": 500.00}
        )

        # Check deposit balance reflects payment
        self.assertEqual(partner_1.customer_deposit_balance, payment.amount)

    def test_open_bo_balance(self):
        """
        Test Blanket Order → Sale Order creation flow with deposits and credit limits.
        """
        self.customer.credit_limit = 400
        partner_1 = self.env["res.partner"].create({"name": "Vandan"})

        # Create supplierinfo for product
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 200,
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "partner_id": partner_1.id,
                "product_id": product.id,
                "delay": 1,
                "min_qty": 1,
                "price": 20,
            }
        )

        # Create blanket order
        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.customer.id,
                "validity_date": fields.Date.to_string(
                    date.today() + timedelta(days=1)
                ),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 1.0,
                            "price_unit": 30.0,
                            "date_schedule": fields.Date.today(),
                        },
                    )
                ],
            }
        )

        # Confirm blanket order
        blanket_order.action_confirm()

        # Trigger scheduled job to release sale orders
        self.blanket_order_obj.create_sale_order_cron()

        # Get sale orders created from blanket order
        view_action = blanket_order.action_view_sale_orders()
        domain_ids = view_action["domain"][0][2]
        sale_order = self.env["sale.order"].browse(domain_ids)

        # Ensure created SOs are linked properly
        self.assertTrue(sale_order)
