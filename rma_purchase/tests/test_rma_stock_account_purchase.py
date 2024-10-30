# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.fields import Date, Datetime
from odoo.tests.common import Form

# pylint: disable=odoo-addons-relative-import
from odoo.addons.rma_account.tests.test_rma_stock_account import TestRmaStockAccount


class TestRmaStockAccountPurchase(TestRmaStockAccount):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pol_model = cls.env["purchase.order.line"]
        cls.po_model = cls.env["purchase.order"]
        cls.rma_operation_supplier_refund = cls.env.ref(
            "rma_account.rma_operation_supplier_refund"
        )
        acc_type = "expense"
        cls.account_price_diff = cls._create_account(
            acc_type, "Refund Price Difference Expense", "rpde", cls.company, False
        )

    def test_01_cost_from_po_move(self):
        """
        Test the price unit is taken from the cost of the stock move associated to
        the PO
        """
        # Create PO:
        self.product_fifo_1.standard_price = 1234
        po = self.po_model.create(
            {
                "partner_id": self.partner_id.id,
            }
        )
        pol_1 = self.pol_model.create(
            {
                "name": self.product_fifo_1.name,
                "order_id": po.id,
                "product_id": self.product_fifo_1.id,
                "product_qty": 20.0,
                "product_uom": self.product_fifo_1.uom_id.id,
                "price_unit": 100.0,
                "date_planned": Datetime.now(),
            }
        )
        po.button_confirm()
        self._do_picking(po.picking_ids)
        self.product_fifo_1.standard_price = 1234  # this should not be taken
        supplier_view = self.env.ref("rma_purchase.view_rma_line_form")
        rma_line = Form(
            self.rma_line.with_context(supplier=1).with_user(self.rma_basic_user),
            view=supplier_view.id,
        )
        rma_line.partner_id = po.partner_id
        rma_line.purchase_order_line_id = pol_1
        rma_line.price_unit = 4356
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._deliver_rma(rma_line)
        # The price is not the standard price, is the value of the incoming layer
        # of the PO
        rma_move_value = picking.move_line_ids.move_id.stock_valuation_layer_ids.value
        po_move_value = po.picking_ids.mapped(
            "move_line_ids.move_id.stock_valuation_layer_ids"
        )[-1].value
        self.assertEqual(-rma_move_value, po_move_value)
        # Test the accounts used
        account_move = (
            picking.move_line_ids.move_id.stock_valuation_layer_ids.account_move_id
        )
        self.check_accounts_used(account_move, "grni", "inventory")
        # Now forcing a refund to check the stock journals
        rma_line.refund_policy = "ordered"
        make_refund = (
            self.env["rma.refund"]
            .with_context(
                **{
                    "customer": True,
                    "active_ids": rma_line.ids,
                    "active_model": "rma.order.line",
                }
            )
            .create({"description": "Test refund"})
        )
        make_refund_res = make_refund.invoice_refund()
        refund_move = (
            self.env["account.move"]
            .browse(make_refund_res["res_id"])
            .line_ids.mapped("move_id")
        )
        refund_move.action_post()
        self.check_accounts_used(refund_move, credit_account="grni")

    def test_02_return_and_refund_ref_po(self):
        """
        Purchase a product.
        Then create an RMA to return it and get the refund from the supplier
        """
        self.product_fifo_1.standard_price = 1234
        po = self.po_model.create(
            {
                "partner_id": self.partner_id.id,
            }
        )
        pol_1 = self.pol_model.create(
            {
                "name": self.product_fifo_1.name,
                "order_id": po.id,
                "product_id": self.product_fifo_1.id,
                "product_qty": 20.0,
                "product_uom": self.product_fifo_1.uom_id.id,
                "price_unit": 100.0,
                "date_planned": Datetime.now(),
            }
        )
        po.button_confirm()
        self._do_picking(po.picking_ids)
        self.product_fifo_1.standard_price = 1234  # this should not be taken
        supplier_view = self.env.ref("rma_purchase.view_rma_line_form")
        rma_line = Form(
            self.rma_line.with_context(supplier=1).with_user(self.rma_basic_user),
            view=supplier_view.id,
        )
        rma_line.partner_id = po.partner_id
        rma_line.purchase_order_line_id = pol_1
        rma_line.price_unit = 4356
        rma_line.operation_id = self.rma_operation_supplier_refund
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        self._deliver_rma(rma_line)
        with Form(
            self.env["account.move"].with_context(default_move_type="in_refund")
        ) as bill_form:
            bill_form.partner_id = rma_line.partner_id
            bill_form.invoice_date = Date.today()
            bill_form.add_rma_line_id = rma_line
        bill = bill_form.save()
        bill.action_post()
        self.assertEqual(len(bill.invoice_line_ids), 1)
        self.assertEqual(bill.invoice_line_ids.rma_line_id, rma_line)
        self.assertEqual(bill.invoice_line_ids.price_unit, pol_1.price_unit)
        self.assertEqual(bill.invoice_line_ids.quantity, 20)
        grni_amls = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.account_grni.id),
                ("rma_line_id", "=", rma_line.id),
            ]
        )
        self.assertEqual(sum(grni_amls.mapped("balance")), 0.0)
        self.assertTrue(all(grni_amls.mapped("reconciled")))

    def test_03_return_and_refund_diff_price(self):
        """
        Purchase a product.
        Then create an RMA to return it and get the refund from the supplier with
        a different price than the original purchase price
        """
        # extra variable to pass pre-commit
        account_pd = self.account_price_diff
        self.product_fifo_1.categ_id.update(
            {"property_account_creditor_price_difference_categ": account_pd}
        )
        self.product_fifo_1.standard_price = 1234
        po = self.po_model.create(
            {
                "partner_id": self.partner_id.id,
            }
        )
        pol_1 = self.pol_model.create(
            {
                "name": self.product_fifo_1.name,
                "order_id": po.id,
                "product_id": self.product_fifo_1.id,
                "product_qty": 10.0,
                "product_uom": self.product_fifo_1.uom_id.id,
                "price_unit": 100.0,
                "date_planned": Datetime.now(),
            }
        )
        po.button_confirm()
        self._do_picking(po.picking_ids)
        self.product_fifo_1.standard_price = 1234  # this should not be taken
        supplier_view = self.env.ref("rma_purchase.view_rma_line_form")
        rma_line = Form(
            self.rma_line.with_context(supplier=1).with_user(self.rma_basic_user),
            view=supplier_view.id,
        )
        rma_line.partner_id = po.partner_id
        rma_line.purchase_order_line_id = pol_1
        rma_line.price_unit = 4356
        rma_line.operation_id = self.rma_operation_supplier_refund
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        self._deliver_rma(rma_line)

        with Form(
            self.env["account.move"].with_context(default_move_type="in_refund")
        ) as bill_form:
            bill_form.partner_id = rma_line.partner_id
            bill_form.invoice_date = Date.today()
            bill_form.add_rma_line_id = rma_line
        bill = bill_form.save()
        bill_form = Form(bill)
        with bill_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 110
        bill = bill_form.save()
        bill.action_post()
        self.assertEqual(len(bill.invoice_line_ids), 1)
        self.assertEqual(bill.invoice_line_ids.rma_line_id, rma_line)
        grni_amls = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.account_grni.id),
                ("rma_line_id", "=", rma_line.id),
            ]
        )
        self.assertEqual(sum(grni_amls.mapped("balance")), 0.0)
        self.assertTrue(all(grni_amls.mapped("reconciled")))
        price_diff_amls = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.account_price_diff.id),
                ("rma_line_id", "=", rma_line.id),
            ]
        )
        self.assertEqual(sum(price_diff_amls.mapped("balance")), -100)
