# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import Form

# pylint: disable=odoo-addons-relative-import
from odoo.addons.rma_account.tests.test_rma_stock_account import TestRmaStockAccount


class TestRmaStockAccountSale(TestRmaStockAccount):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_receive_refund = cls.env.ref(
            "rma_account.rma_operation_customer_refund"
        )
        customer1 = cls.env["res.partner"].create({"name": "Customer 1"})
        cls.product_fifo_1.standard_price = 1234
        cls._create_inventory(cls.product_fifo_1, 20.0, cls.env.ref("rma.location_rma"))
        cls.so1 = cls.env["sale.order"].create(
            {
                "partner_id": customer1.id,
                "partner_invoice_id": customer1.id,
                "partner_shipping_id": customer1.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product_fifo_1.name,
                            "product_id": cls.product_fifo_1.id,
                            "product_uom_qty": 20.0,
                            "product_uom": cls.product_fifo_1.uom_id.id,
                            "price_unit": 800,
                        },
                    ),
                ],
            }
        )
        cls.so1.action_confirm()
        for ml in cls.so1.picking_ids.move_line_ids:
            ml.quantity = ml.quantity_product_uom
            ml.picked = True
        cls.so1.picking_ids.button_validate()

    def test_01_cost_from_so_move(self):
        """
        Test the price unit is taken from the cost of the stock move associated to
        the SO
        """
        so_line = self.so1.order_line.filtered(
            lambda r: r.product_id == self.product_fifo_1
        )
        self.product_fifo_1.standard_price = 5678  # this should not be taken
        customer_view = self.env.ref("rma_sale.view_rma_line_form")
        rma_line = Form(
            self.rma_line.with_context(customer=1).with_user(self.rma_basic_user),
            view=customer_view.id,
        )
        rma_line.partner_id = self.so1.partner_id
        rma_line.sale_line_id = so_line
        rma_line.price_unit = 4356
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._receive_rma(rma_line)
        # The price is not the standard price, is the value of the outgoing layer
        # of the SO
        rma_move_value = picking.move_ids.stock_valuation_layer_ids.value
        so_move_value = self.so1.picking_ids.mapped(
            "move_ids.stock_valuation_layer_ids"
        )[-1].value
        self.assertEqual(rma_move_value, -so_move_value)
        # Test the accounts used
        account_move = picking.move_ids.stock_valuation_layer_ids.account_move_id
        self.check_accounts_used(
            account_move, debit_account="inventory", credit_account="gdni"
        )

    def test_02_return_and_refund_ref_so(self):
        """
        Sell a product. Create a customer invoice.
        Then create an RMA to return it and refund to the customer
        """
        customer_view = self.env.ref("rma_sale.view_rma_line_form")
        so_line = self.so1.order_line.filtered(
            lambda r: r.product_id == self.product_fifo_1
        )
        rma_line = Form(
            self.rma_line.with_context(customer=1).with_user(self.rma_basic_user),
            view=customer_view.id,
        )
        rma_line.partner_id = self.so1.partner_id
        rma_line.sale_line_id = so_line
        rma_line.operation_id = self.operation_receive_refund
        rma_line.price_unit = 4356  # This should never be used
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        self._receive_rma(rma_line)
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.item_ids.qty_to_refund = 20
        make_refund.invoice_refund()
        refund = rma_line.refund_line_ids.move_id
        refund.action_post()
        self.assertEqual(refund.invoice_line_ids[0].price_unit, so_line.price_unit)
        self.assertEqual(refund.invoice_line_ids[0].currency_id, so_line.currency_id)
        gdni_amls = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.account_gdni.id),
                ("rma_line_id", "=", rma_line.id),
            ]
        )
        self.assertEqual(sum(gdni_amls.mapped("balance")), 0.0)
        self.assertTrue(all(gdni_amls.mapped("reconciled")))

    def test_03_return_and_refund_ref_inv(self):
        """
        Sell a product. Then create an RMA to return it and refund to the customer
        """
        customer_invoice = self.so1._create_invoices()
        customer_view = self.env.ref("rma_sale.view_rma_line_form")
        so_line = self.so1.order_line.filtered(
            lambda r: r.product_id == self.product_fifo_1
        )
        rma_line = Form(
            self.rma_line.with_context(customer=1).with_user(self.rma_basic_user),
            view=customer_view.id,
        )
        rma_line.partner_id = self.so1.partner_id
        rma_line.account_move_line_id = customer_invoice.invoice_line_ids[0]
        rma_line.operation_id = self.operation_receive_refund
        rma_line.price_unit = 4356  # This should never be used
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        self._receive_rma(rma_line)
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.item_ids.qty_to_refund = 20
        make_refund.invoice_refund()
        refund = rma_line.refund_line_ids.move_id
        refund.action_post()
        self.assertEqual(refund.invoice_line_ids[0].price_unit, so_line.price_unit)
        self.assertEqual(refund.invoice_line_ids[0].currency_id, so_line.currency_id)
        gdni_amls = self.env["account.move.line"].search(
            [
                ("account_id", "=", self.account_gdni.id),
                ("rma_line_id", "=", rma_line.id),
            ]
        )
        self.assertEqual(sum(gdni_amls.mapped("balance")), 0.0)
        self.assertTrue(all(gdni_amls.mapped("reconciled")))
