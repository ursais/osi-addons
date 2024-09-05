# Copyright 2016-20 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields

from odoo.addons.stock_request.tests.test_stock_request import TestStockRequest


class TestStockRequestPurchase(TestStockRequest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.route_buy = cls.warehouse.buy_pull_id.route_id
        cls.supplier = cls.env["res.partner"].create({"name": "Supplier"})
        cls.product.write(
            {
                "route_ids": [(6, 0, cls.route_buy.ids)],
                "seller_ids": [(0, 0, {"partner_id": cls.supplier.id, "delay": 5})],
            }
        )

    def test_create_request_01(self):
        """Single Stock request with buy rule"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }

        order = (
            self.env["stock.request.order"]
            .with_user(self.stock_request_user)
            .create(vals)
        )

        order.action_confirm()
        self.assertEqual(order.state, "open")
        self.assertEqual(order.stock_request_ids.state, "open")

        order.invalidate_recordset()
        self.assertEqual(len(order.sudo().purchase_ids), 1)
        self.assertEqual(len(order.picking_ids), 0)
        self.assertEqual(len(order.move_ids), 0)
        self.assertEqual(len(order.stock_request_ids.sudo().purchase_ids), 1)
        self.assertEqual(len(order.stock_request_ids.picking_ids), 0)
        self.assertEqual(len(order.stock_request_ids.move_ids), 0)
        self.assertEqual(order.stock_request_ids.qty_in_progress, 0.0)

        purchase = order.sudo().purchase_ids[0]
        self.assertEqual(purchase.company_id, order.stock_request_ids[0].company_id)
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.action_confirm()

        self.assertEqual(order.stock_request_ids.qty_in_progress, 5.0)
        self.assertEqual(order.stock_request_ids.qty_done, 0.0)

        picking.action_assign()
        packout1 = picking.move_line_ids[0]
        packout1.quantity = 5
        picking.button_validate()

        self.assertEqual(order.stock_request_ids.qty_in_progress, 0.0)
        self.assertEqual(
            order.stock_request_ids.qty_done, order.stock_request_ids.product_uom_qty
        )
        self.assertEqual(order.stock_request_ids.state, "done")
        self.assertEqual(order.state, "done")

    def test_create_request_02(self):
        """Multiple Stock requests with buy rule"""
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 5.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
        }

        stock_request_1 = self.stock_request.with_user(self.stock_request_user).create(
            vals
        )
        stock_request_2 = self.stock_request.with_user(
            self.stock_request_manager
        ).create(vals)

        stock_request_1.action_confirm()
        self.assertEqual(
            sum(stock_request_1.sudo().purchase_line_ids.mapped("product_qty")), 5
        )

        stock_request_2.with_user(self.stock_request_manager).sudo().action_confirm()

        self.assertEqual(
            sum(stock_request_2.sudo().purchase_line_ids.mapped("product_qty")), 10
        )

        stock_request_1.invalidate_recordset()
        stock_request_2.invalidate_recordset()

        self.assertEqual(len(stock_request_1.sudo().purchase_ids), 1)
        self.assertEqual(len(stock_request_2.sudo().purchase_ids), 1)
        self.assertEqual(len(stock_request_1.sudo().purchase_ids), 1)
        self.assertEqual(len(stock_request_2.sudo().purchase_line_ids), 1)
        self.assertEqual(
            stock_request_1.sudo().purchase_ids, stock_request_2.sudo().purchase_ids
        )
        self.assertEqual(
            stock_request_1.sudo().purchase_line_ids,
            stock_request_2.sudo().purchase_line_ids,
        )

        purchase = stock_request_1.sudo().purchase_ids[0]

        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.action_confirm()

        self.assertEqual(stock_request_1.qty_in_progress, 5.0)
        self.assertEqual(stock_request_1.qty_done, 0.0)
        self.assertEqual(stock_request_2.qty_in_progress, 5.0)
        self.assertEqual(stock_request_2.qty_done, 0.0)

        picking.action_assign()
        packout1 = picking.move_line_ids[0]
        packout1.quantity = 10
        picking.button_validate()

        self.assertEqual(stock_request_1.qty_in_progress, 0.0)
        self.assertEqual(stock_request_1.qty_done, stock_request_1.product_uom_qty)

        self.assertEqual(stock_request_2.qty_in_progress, 0.0)
        self.assertEqual(stock_request_2.qty_done, stock_request_2.product_uom_qty)

    def test_create_request_cancel_purchase(self):
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 5.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
        }
        stock_request = self.stock_request.with_user(self.stock_request_user).create(
            vals
        )
        stock_request.action_confirm()
        self.assertEqual(stock_request.purchase_ids.state, "draft")
        stock_request.action_cancel()
        self.assertEqual(stock_request.purchase_ids.state, "cancel")

    def test_view_actions(self):
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }

        order = self.env["stock.request.order"].sudo().create(vals)

        order.action_confirm()

        stock_request = order.stock_request_ids

        action = stock_request.action_view_purchase()

        self.assertEqual(action["domain"], "[]")
        self.assertEqual("views" in action.keys(), True)
        self.assertEqual(action["res_id"], stock_request.purchase_ids[0].id)

        action = stock_request.purchase_ids[0].action_view_stock_request()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_id"], stock_request.id)

        action = order.action_view_purchase()

        self.assertEqual(action["domain"], "[]")
        self.assertEqual("views" in action.keys(), True)
        self.assertEqual(action["res_id"], order.purchase_ids[0].id)
