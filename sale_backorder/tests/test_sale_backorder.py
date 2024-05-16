# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from dateutil.relativedelta import relativedelta as rdelta

from odoo.tests.common import TransactionCase


class TestSaleBackorderCommon(TransactionCase):
    def setUp(self):
        super(TestSaleBackorderCommon, self).setUp()
        self.SaleOrder = self.env["sale.order"]
        self.sobackorder_wiz = self.env["sobackorder.report.wizard"]
        self.fsm_per_order_1 = self.env["product.product"].create(
            {
                "name": "FSM Order per Sale Order #1",
                "categ_id": self.env.ref("product.product_category_3").id,
                "standard_price": 85.0,
                "list_price": 90.0,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "invoice_policy": "order",
            }
        )
        self.fsm_per_order_2 = self.env["product.product"].create(
            {
                "name": "FSM Order per Sale Order #1",
                "categ_id": self.env.ref("product.product_category_3").id,
                "standard_price": 85.0,
                "list_price": 90.0,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "invoice_policy": "order",
            }
        )
        self.partner_customer_usd = self.env["res.partner"].create(
            {
                "name": "partner_a",
                "company_id": False,
            }
        )
        self.default_account_revenue = self.env["account.account"].search(
            [
                ("company_id", "=", self.env.user.company_id.id),
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_revenue").id,
                ),
            ],
            limit=1,
        )
        self.default_journal_sale = self.env["account.journal"].search(
            [("company_id", "=", self.env.user.company_id.id), ("type", "=", "sale")],
            limit=1,
        )
        self.pricelist_usd = self.env["product.pricelist"].search(
            [("currency_id.name", "=", "USD")], limit=1
        )
        # create a generic Sale Order with one product
        self.sale_order_1 = self.SaleOrder.create(
            {
                "partner_id": self.partner_customer_usd.id,
                "pricelist_id": self.pricelist_usd.id,
                "last_date_delivered": datetime.now(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.fsm_per_order_1.name,
                            "product_id": self.fsm_per_order_1.id,
                            "product_uom_qty": 1,
                            "product_uom": self.fsm_per_order_1.uom_id.id,
                            "price_unit": self.fsm_per_order_1.list_price,
                            "tax_id": False,
                            "uigd_value": 1.0,
                            "bo_value": 1.0,
                            "bo_qty": 1.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self.fsm_per_order_2.name,
                            "product_id": self.fsm_per_order_2.id,
                            "product_uom_qty": 1,
                            "product_uom": self.fsm_per_order_2.uom_id.id,
                            "price_unit": self.fsm_per_order_2.list_price,
                            "tax_id": False,
                            "uigd_value": 1.0,
                            "bo_value": 1.0,
                            "bo_qty": 1.0,
                            "last_date_delivered": datetime.now() + rdelta(days=15),
                        },
                    ),
                ],
            }
        )

    def test_so_wizard(self):
        self.sobackorder_wiz.action_print_report()

    def test_sale_order(self):
        for line in self.sale_order_1.order_line:
            line.last_date_delivered = datetime.now()
            line.last_bill_date = datetime.now()
        self.sale_order_1._compute_uigd_value()
        self.sale_order_1._compute_bo_value()
        self.sale_order_1._compute_last_date_delivered()
        self.sale_order_1._compute_last_bill_date()

    def test_sale_order_order_line(self):
        self.sale_order_1.action_confirm()
        self.context = {
            "active_model": "sale.order",
            "active_ids": [self.sale_order_1.id],
            "active_id": self.sale_order_1.id,
            "default_journal_id": self.default_journal_sale.id,
        }

        downpayment = (
            self.env["sale.advance.payment.inv"]
            .with_context(self.context)
            .create(
                {
                    "advance_payment_method": "fixed",
                    "fixed_amount": 50,
                    "deposit_account_id": self.default_account_revenue.id,
                }
            )
        )
        downpayment.create_invoices()

        for line in self.sale_order_1.order_line:
            for move in line.move_ids:
                move.picking_id.write({"state": "done"})
                move.write({"state": "done"})
                move.to_refund = True
            line._compute_bo_qty()
            line._compute_uigd_qty()
            line._compute_uigd_value()
            line._compute_bo_value()
            line._compute_last_date_delivered()
            line._compute_last_bill_date()

    def test_sale_order_line_method(self):
        self.sale_order_1.action_confirm()
        self.invoice = self.sale_order_1._create_invoices()
        self.invoice.action_post()
        self.invoice.action_reverse()
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=self.invoice.ids)
            .create(
                {
                    "date": datetime.today(),
                    "reason": "no reason",
                    "refund_method": "refund",
                }
            )
        )
        move_reversal.reverse_moves()
        for line in self.sale_order_1.order_line:
            for move in line.move_ids:
                move.picking_id.write({"state": "done"})
                move.write({"state": "done"})
                move.to_refund = True
            line._compute_last_bill_date()
