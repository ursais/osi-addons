# Copyright 2017 ForgeFlow S.L.
# Copyright 2022-2023 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from collections import Counter
from datetime import datetime

from odoo import exceptions, fields
from odoo.tests import common, new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestStockRequest(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # common models
        cls.stock_request = cls.env["stock.request"]
        cls.request_order = cls.env["stock.request.order"]
        # refs
        cls.stock_request_user_group = cls.env.ref(
            "stock_request.group_stock_request_user"
        )
        cls.main_company = cls.env.ref("base.main_company")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")
        cls.virtual_loc = cls.env.ref("stock.stock_location_customers")
        # common data
        cls.company_2 = cls.env["res.company"].create(
            {"name": "Comp2", "parent_id": cls.main_company.id}
        )
        cls.company_2_address = (
            cls.env["res.partner"]
            .with_context(company_id=cls.company_2.id)
            .create({"name": "Peñiscola"})
        )
        cls.wh2 = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_2.id)], limit=1
        )
        cls.stock_request_user = new_test_user(
            cls.env,
            login="stock_request_user",
            groups="stock_request.group_stock_request_user",
            company_ids=[(4, cls.main_company.id), (4, cls.company_2.id)],
        )
        cls.stock_request_manager = new_test_user(
            cls.env,
            login="stock_request_manager",
            groups="stock_request.group_stock_request_manager",
            company_ids=[(4, cls.main_company.id), (4, cls.company_2.id)],
        )
        cls.product = cls._create_product("SH", "Shoes", False)
        cls.product_company_2 = cls._create_product("SH_2", "Shoes", cls.company_2.id)

        cls.ressuply_loc = cls._create_location(
            name="Ressuply",
            location_id=cls.warehouse.view_location_id.id,
            company_id=cls.main_company.id,
        )
        cls.ressuply_loc_2 = cls._create_location(
            name="Ressuply",
            location_id=cls.wh2.view_location_id.id,
            company_id=cls.company_2.id,
        )

        cls.route = cls._create_route(name="Transfer", company_id=cls.main_company.id)
        cls.route_2 = cls._create_route(name="Transfer", company_id=cls.company_2.id)
        cls.route_3 = cls._create_route(name="Transfer", company_id=cls.main_company.id)
        cls.uom_dozen = cls.env["uom.uom"].create(
            {
                "name": "Test-DozenA",
                "category_id": cls.categ_unit.id,
                "factor_inv": 12,
                "uom_type": "bigger",
                "rounding": 0.001,
            }
        )

        cls.env["stock.rule"].create(
            {
                "name": "Transfer",
                "route_id": cls.route.id,
                "location_src_id": cls.ressuply_loc.id,
                "location_dest_id": cls.warehouse.lot_stock_id.id,
                "action": "pull",
                "picking_type_id": cls.warehouse.int_type_id.id,
                "procure_method": "make_to_stock",
                "warehouse_id": cls.warehouse.id,
                "company_id": cls.main_company.id,
            }
        )

        cls.env["stock.rule"].create(
            {
                "name": "Transfer",
                "route_id": cls.route_2.id,
                "location_src_id": cls.ressuply_loc_2.id,
                "location_dest_id": cls.wh2.lot_stock_id.id,
                "action": "pull",
                "picking_type_id": cls.wh2.int_type_id.id,
                "procure_method": "make_to_stock",
                "warehouse_id": cls.wh2.id,
                "company_id": cls.company_2.id,
            }
        )

        cls.env["ir.config_parameter"].sudo().set_param(
            "stock.no_auto_scheduler", "True"
        )

    @classmethod
    def _create_product(cls, default_code, name, company_id, **vals):
        return cls.env["product.product"].create(
            dict(
                name=name,
                default_code=default_code,
                uom_id=cls.env.ref("uom.product_uom_unit").id,
                company_id=company_id,
                type="product",
                **vals,
            )
        )

    @classmethod
    def _create_product_template_attribute_line(
        cls, product_tmpl_id, attribute_id, value_id
    ):
        return cls.env["product.template.attribute.line"].create(
            {
                "product_tmpl_id": product_tmpl_id,
                "attribute_id": attribute_id,
                "value_ids": value_id,
            }
        )

    @classmethod
    def _create_product_attribute_value(cls, name, attribute):
        return cls.env["product.attribute.value"].create(
            {"name": name, "attribute_id": attribute}
        )

    @classmethod
    def _create_product_attribute(cls, name):
        return cls.env["product.attribute"].create({"name": name})

    @classmethod
    def _create_location(cls, **vals):
        return cls.env["stock.location"].create(dict(usage="internal", **vals))

    @classmethod
    def _create_route(cls, **vals):
        return cls.env["stock.route"].create(
            dict(
                product_categ_selectable=False,
                product_selectable=True,
                sequence=10,
                **vals,
            )
        )


class TestStockRequestBase(TestStockRequest):
    def _create_stock_quant(self, product, location, qty):
        self.env["stock.quant"].create(
            {"product_id": product.id, "location_id": location.id, "quantity": qty}
        )

    def test_defaults(self):
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 5.0,
        }
        stock_request = (
            self.stock_request.with_user(self.stock_request_user)
            .with_context(company_id=self.main_company.id)
            .create(vals)
        )

        self.assertEqual(stock_request.requested_by, self.stock_request_user)

        self.assertEqual(stock_request.warehouse_id, self.warehouse)

        self.assertEqual(stock_request.location_id, self.warehouse.lot_stock_id)

    def test_defaults_order(self):
        vals = {}
        order = (
            self.request_order.with_user(self.stock_request_user)
            .with_context(company_id=self.main_company.id)
            .create(vals)
        )

        self.assertEqual(order.requested_by, self.stock_request_user)

        self.assertEqual(order.warehouse_id, self.warehouse)

        self.assertEqual(order.location_id, self.warehouse.lot_stock_id)

    def test_onchanges_order(self):
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
        order = self.request_order.with_user(self.stock_request_user).new(vals)
        self.stock_request_user.company_id = self.company_2
        order.company_id = self.company_2

        order.onchange_company_id()

        stock_request = order.stock_request_ids
        self.assertEqual(order.warehouse_id, self.wh2)
        self.assertEqual(order.location_id, self.wh2.lot_stock_id)
        self.assertEqual(order.warehouse_id, stock_request.warehouse_id)

        procurement_group = self.env["procurement.group"].create({"name": "TEST"})
        order.procurement_group_id = procurement_group
        order.onchange_procurement_group_id()
        self.assertEqual(
            order.procurement_group_id, order.stock_request_ids.procurement_group_id
        )

        order.procurement_group_id = procurement_group
        order.onchange_procurement_group_id()
        self.assertEqual(
            order.procurement_group_id, order.stock_request_ids.procurement_group_id
        )
        order.picking_policy = "one"

        order.onchange_picking_policy()
        self.assertEqual(order.picking_policy, order.stock_request_ids.picking_policy)

        order.expected_date = datetime.now()
        order.onchange_expected_date()
        self.assertEqual(order.expected_date, order.stock_request_ids.expected_date)

        order.requested_by = self.stock_request_manager
        order.onchange_requested_by()
        self.assertEqual(order.requested_by, order.stock_request_ids.requested_by)

    def test_onchanges(self):
        self.product.route_ids = [(6, 0, self.route.ids)]
        vals = {
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 5.0,
            "company_id": self.main_company.id,
        }
        stock_request = self.stock_request.with_user(self.stock_request_user).new(vals)
        stock_request.product_id = self.product
        vals = stock_request.default_get(["warehouse_id", "company_id"])
        stock_request.update(vals)
        stock_request.onchange_product_id()
        self.assertIn(self.route.id, stock_request.route_ids.ids)

        self.stock_request_user.company_id = self.company_2
        stock_request.company_id = self.company_2
        stock_request.onchange_company_id()

        self.assertEqual(stock_request.warehouse_id, self.wh2)
        self.assertEqual(stock_request.location_id, self.wh2.lot_stock_id)

        product = self.env["product.product"].create(
            {
                "name": "Wheat",
                "uom_id": self.env.ref("uom.product_uom_kgm").id,
                "uom_po_id": self.env.ref("uom.product_uom_kgm").id,
            }
        )

        # Test onchange_product_id
        stock_request.product_id = product
        stock_request.onchange_product_id()

        self.assertEqual(
            stock_request.product_uom_id, self.env.ref("uom.product_uom_kgm")
        )

        stock_request.product_id = self.env["product.product"]

        # Test onchange_warehouse_id
        wh2_2 = (
            self.env["stock.warehouse"]
            .with_context(company_id=self.company_2.id)
            .create(
                {
                    "name": "C2_2",
                    "code": "C2_2",
                    "company_id": self.company_2.id,
                    "partner_id": self.company_2_address.id,
                }
            )
        )
        stock_request.warehouse_id = wh2_2
        stock_request.onchange_warehouse_id()

        self.assertEqual(stock_request.warehouse_id, wh2_2)

        self.stock_request_user.company_id = self.main_company
        stock_request.warehouse_id = self.warehouse
        stock_request.onchange_warehouse_id()

        self.assertEqual(stock_request.company_id, self.main_company)
        self.assertEqual(stock_request.location_id, self.warehouse.lot_stock_id)

    def test_stock_request_order_validations_01(self):
        """Testing the discrepancy in warehouse_id between
        stock request and order"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.wh2.id,
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
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_validations_02(self):
        """Testing the discrepancy in location_id between
        stock request and order"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.wh2.lot_stock_id.id,
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
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_validations_03(self):
        """Testing the discrepancy in requested_by between
        stock request and order"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "requested_by": self.stock_request_user.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "requested_by": self.stock_request_manager.id,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_validations_04(self):
        """Testing the discrepancy in procurement_group_id between
        stock request and order"""
        procurement_group = self.env["procurement.group"].create(
            {"name": "Procurement"}
        )
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "procurement_group_id": procurement_group.id,
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
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_validations_05(self):
        """Testing the discrepancy in company between
        stock request and order"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.company_2.id,
            "warehouse_id": self.wh2.id,
            "location_id": self.wh2.lot_stock_id.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.company_2.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_validations_06(self):
        """Testing the discrepancy in expected dates between
        stock request and order"""
        expected_date = fields.Datetime.now()
        child_expected_date = "2015-01-01"
        vals = {
            "company_id": self.company_2.id,
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
                        "expected_date": child_expected_date,
                    },
                )
            ],
        }
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.create(vals)

    def test_stock_request_order_validations_07(self):
        """Testing the discrepancy in picking policy between
        stock request and order"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "picking_policy": "one",
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
        with self.assertRaises(exceptions.ValidationError):
            self.request_order.with_user(self.stock_request_user).create(vals)

    def test_stock_request_order_available_stock_01(self):
        self.main_company.stock_request_check_available_first = True
        self._create_stock_quant(self.product, self.warehouse.lot_stock_id, 6)
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
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        order.action_confirm()
        self.assertEqual(order.stock_request_ids.state, "done")
        self.assertEqual(order.state, "done")
        self.assertEqual(len(order.stock_request_ids.move_ids), 1)
        quant_stock = self.product.stock_quant_ids.filtered(
            lambda x: x.location_id == self.warehouse.lot_stock_id
        )
        self.assertEqual(quant_stock.quantity, 6)

    def test_stock_request_order_available_stock_02(self):
        self.main_company.stock_request_check_available_first = True
        self.location_child_1 = self._create_location(
            name="Child 1",
            location_id=self.warehouse.lot_stock_id.id,
            company_id=self.main_company.id,
        )
        self.location_child_2 = self._create_location(
            name="Child 2",
            location_id=self.warehouse.lot_stock_id.id,
            company_id=self.main_company.id,
        )
        self._create_stock_quant(self.product, self.location_child_1, 6)
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.location_child_1.id,
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
                        "location_id": self.location_child_1.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        order.action_confirm()
        self.assertEqual(order.stock_request_ids.state, "done")
        self.assertEqual(order.state, "done")
        self.assertEqual(len(order.stock_request_ids.move_ids), 1)

    def test_stock_request_order_available_stock_03(self):
        self.main_company.stock_request_check_available_first = True
        self.location_child_1 = self._create_location(
            name="Child 1",
            location_id=self.warehouse.lot_stock_id.id,
            company_id=self.main_company.id,
        )
        self.location_child_2 = self._create_location(
            name="Child 2",
            location_id=self.warehouse.lot_stock_id.id,
            company_id=self.main_company.id,
        )
        self._create_stock_quant(self.product, self.location_child_1, 3)
        self._create_stock_quant(self.product, self.location_child_2, 2)
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
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        order.action_confirm()
        self.assertEqual(order.stock_request_ids.state, "done")
        self.assertEqual(order.state, "done")
        self.assertEqual(len(order.stock_request_ids.move_ids), 2)

    def test_stock_request_validations_01(self):
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.env.ref("uom.product_uom_kgm").id,
            "product_uom_qty": 5.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
        }
        # Select a UoM that is incompatible with the product's UoM
        with self.assertRaises(exceptions.ValidationError):
            self.stock_request.with_user(self.stock_request_user).create(vals)

    def test_create_request_01(self):
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

        order = self.request_order.with_user(self.stock_request_user).create(vals)

        stock_request = order.stock_request_ids

        self.product.route_ids = [(6, 0, self.route.ids)]
        order.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(order.state, "open")
        self.assertEqual(stock_request.state, "open")

        self.assertEqual(len(order.picking_ids), 1)
        self.assertEqual(len(order.move_ids), 1)
        self.assertEqual(len(stock_request.picking_ids), 1)
        self.assertEqual(len(stock_request.move_ids), 1)
        self.assertEqual(
            stock_request.move_ids[0].location_dest_id, stock_request.location_id
        )
        self.assertEqual(stock_request.qty_in_progress, stock_request.product_uom_qty)
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.ressuply_loc.id,
                "quantity": 5.0,
            }
        )
        picking = stock_request.picking_ids[0]
        picking.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(stock_request.qty_in_progress, 5.0)
        self.assertEqual(stock_request.qty_done, 0.0)
        picking.with_user(self.stock_request_manager).action_assign()
        self.assertEqual(picking.origin, order.name)
        packout1 = picking.move_line_ids[0]
        packout1.quantity = 5
        packout1.picked = True
        picking.with_user(self.stock_request_manager)._action_done()
        self.assertEqual(stock_request.qty_in_progress, 0.0)
        self.assertEqual(stock_request.qty_done, stock_request.product_uom_qty)
        self.assertEqual(order.state, "done")
        self.assertEqual(stock_request.state, "done")

    def test_create_request_02(self):
        """Use different UoM's"""

        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.uom_dozen.id,
            "product_uom_qty": 1.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
        }

        stock_request = self.stock_request.with_user(self.stock_request_user).create(
            vals
        )

        self.product.route_ids = [(6, 0, self.route.ids)]
        stock_request.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(stock_request.state, "open")
        self.assertEqual(len(stock_request.picking_ids), 1)
        self.assertEqual(len(stock_request.move_ids), 1)
        self.assertEqual(
            stock_request.move_ids[0].location_dest_id, stock_request.location_id
        )
        self.assertEqual(stock_request.qty_in_progress, stock_request.product_uom_qty)
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.ressuply_loc.id,
                "quantity": 12.0,
            }
        )
        picking = stock_request.picking_ids[0]
        picking.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(stock_request.qty_in_progress, 1.0)
        self.assertEqual(stock_request.qty_done, 0.0)
        picking.with_user(self.stock_request_manager).action_assign()
        packout1 = picking.move_line_ids[0]
        packout1.quantity = 1
        packout1.picked = True
        picking.with_user(self.stock_request_manager)._action_done()
        self.assertEqual(stock_request.qty_in_progress, 0.0)
        self.assertEqual(stock_request.qty_done, stock_request.product_uom_qty)
        self.assertEqual(stock_request.state, "done")

    def test_create_request_03(self):
        """Multiple stock requests"""
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 4.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
        }

        stock_request_1 = (
            self.env["stock.request"].with_user(self.stock_request_user).create(vals)
        )
        stock_request_2 = (
            self.env["stock.request"]
            .with_user(self.stock_request_manager.id)
            .create(vals)
        )
        stock_request_2.product_uom_qty = 6.0
        self.product.route_ids = [(6, 0, self.route.ids)]
        stock_request_1.sudo().action_confirm()
        stock_request_2.sudo().action_confirm()
        self.assertEqual(len(stock_request_1.sudo().picking_ids), 1)
        self.assertEqual(
            stock_request_1.sudo().picking_ids, stock_request_2.sudo().picking_ids
        )
        self.assertEqual(
            stock_request_1.sudo().move_ids, stock_request_2.sudo().move_ids
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.ressuply_loc.id,
                "quantity": 10.0,
            }
        )
        picking = stock_request_1.sudo().picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(stock_request_1.qty_in_progress, 4)
        self.assertEqual(stock_request_1.qty_done, 0)
        self.assertEqual(stock_request_1.qty_cancelled, 0)
        self.assertEqual(stock_request_2.qty_in_progress, 6)
        self.assertEqual(stock_request_2.qty_done, 0)
        self.assertEqual(stock_request_2.qty_cancelled, 0)
        packout1 = picking.move_line_ids[0]
        packout1.quantity = 4
        packout1.picked = True
        self.env["stock.backorder.confirmation"].with_context(
            button_validate_picking_ids=[picking.id]
        ).create({"pick_ids": [(4, picking.id)]}).process_cancel_backorder()
        self.assertEqual(stock_request_1.qty_in_progress, 0)
        self.assertEqual(stock_request_1.qty_done, 4)
        self.assertEqual(stock_request_1.qty_cancelled, 0)
        self.assertEqual(stock_request_1.state, "done")
        self.assertEqual(stock_request_2.qty_in_progress, 0)
        self.assertEqual(stock_request_2.qty_done, 0)
        self.assertEqual(stock_request_2.qty_cancelled, 6)
        self.assertEqual(stock_request_2.state, "cancel")

    def test_cancel_request(self):
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

        order = self.request_order.with_user(self.stock_request_user).create(vals)

        self.product.route_ids = [(6, 0, self.route.ids)]
        order.with_user(self.stock_request_manager).action_confirm()
        stock_request = order.stock_request_ids
        self.assertEqual(len(order.picking_ids), 1)
        self.assertEqual(len(order.move_ids), 1)
        self.assertEqual(len(stock_request.picking_ids), 1)
        self.assertEqual(len(stock_request.move_ids), 1)
        self.assertEqual(
            stock_request.move_ids[0].location_dest_id, stock_request.location_id
        )
        self.assertEqual(stock_request.qty_in_progress, stock_request.product_uom_qty)
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.ressuply_loc.id,
                "quantity": 5.0,
            }
        )
        picking = stock_request.picking_ids[0]
        picking.with_user(self.stock_request_user).action_confirm()
        self.assertEqual(stock_request.qty_in_progress, 5.0)
        self.assertEqual(stock_request.qty_done, 0.0)
        picking.with_user(self.stock_request_manager).action_assign()
        order.with_user(self.stock_request_manager).action_cancel()

        self.assertEqual(stock_request.qty_in_progress, 0.0)
        self.assertEqual(stock_request.qty_done, 0.0)
        self.assertEqual(len(stock_request.picking_ids), 0)

        # Set the request back to draft
        order.with_user(self.stock_request_user).action_draft()
        self.assertEqual(order.state, "draft")
        self.assertEqual(stock_request.state, "draft")

        # Re-confirm. We expect new pickings to be created
        order.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(len(stock_request.picking_ids), 1)
        self.assertEqual(len(stock_request.move_ids), 2)

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

        order = self.request_order.create(vals)
        self.product.route_ids = [(6, 0, self.route.ids)]

        order.with_user(self.stock_request_manager).action_confirm()
        stock_request = order.stock_request_ids
        self.assertTrue(stock_request.picking_ids)
        self.assertTrue(order.picking_ids)

        action = order.action_view_transfer()
        self.assertEqual("domain" in action.keys(), True)
        self.assertEqual("views" in action.keys(), True)
        self.assertEqual(action["res_id"], order.picking_ids[0].id)

        action = order.action_view_stock_requests()
        self.assertEqual("domain" in action.keys(), True)
        self.assertEqual("views" in action.keys(), True)
        self.assertEqual(action["res_id"], stock_request[0].id)

        action = stock_request.action_view_transfer()
        self.assertEqual("domain" in action.keys(), True)
        self.assertEqual("views" in action.keys(), True)
        self.assertEqual(action["res_id"], stock_request.picking_ids[0].id)

        action = stock_request.picking_ids[0].action_view_stock_request()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_id"], stock_request.id)

    def test_stock_request_constrains(self):
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

        # Cannot assign a warehouse that belongs to another company
        with self.assertRaises(exceptions.ValidationError):
            stock_request.warehouse_id = self.wh2
        # Cannot assign a product that belongs to another company
        with self.assertRaises(exceptions.ValidationError):
            stock_request.product_id = self.product_company_2
        # Cannot assign a location that belongs to another company
        with self.assertRaises(exceptions.ValidationError):
            stock_request.location_id = self.wh2.lot_stock_id
        # Cannot assign a route that belongs to another company
        with self.assertRaises(exceptions.ValidationError):
            stock_request.route_id = self.route_2

    def test_stock_request_order_from_products(self):
        template_a = self.env["product.template"].create({"name": "ProductTemplate"})
        product_attribute = self._create_product_attribute("Attribute")
        product_att_value = self._create_product_attribute_value(
            "Name-1", product_attribute.id
        )
        product_tmpl_att_line = self._create_product_template_attribute_line(
            template_a.id, product_attribute.id, product_att_value
        )
        template_a.attribute_line_ids |= product_tmpl_att_line
        product_tmpl_att_value = self.env["product.template.attribute.value"].search(
            []
        )[-1]
        product_a1 = self.env["product.product"].search(
            [
                (
                    "product_template_variant_value_ids.name",
                    "=",
                    product_tmpl_att_value.name,
                )
            ]
        )
        product_att_value = self._create_product_attribute_value(
            "Name-2", product_attribute.id
        )
        template_a.attribute_line_ids.value_ids |= product_att_value
        product_a2 = self.env["product.product"].search(
            [("product_template_variant_value_ids.name", "=", product_att_value.name)]
        )
        product_att_value = self._create_product_attribute_value(
            "Name-3", product_attribute.id
        )
        template_a.attribute_line_ids.value_ids |= product_att_value
        product_a3 = self.env["product.product"].search(
            [("product_template_variant_value_ids.name", "=", product_att_value.name)]
        )
        product_b1 = self._create_product("CODEB1", "Product B1", self.main_company.id)
        template_b = product_b1.product_tmpl_id
        # One archived variant of B
        self._create_product(
            "CODEB2",
            "Product B2",
            self.main_company.id,
            product_tmpl_id=template_b.id,
            active=False,
        )
        order = self.request_order

        # Selecting some variants and creating an order
        preexisting = order.search([])
        wanted_products = product_a1 + product_a2 + product_b1
        action = order._create_from_product_multiselect(wanted_products)
        new_order = order.search([]) - preexisting
        self.assertEqual(len(new_order), 1)
        self.assertEqual(
            action["res_id"],
            new_order.id,
            msg="Returned action references the wrong record",
        )
        self.assertEqual(
            Counter(wanted_products),
            Counter(new_order.stock_request_ids.mapped("product_id")),
            msg="Not all wanted products were ordered",
        )

        # Selecting a template and creating an order
        preexisting = order.search([])
        action = order._create_from_product_multiselect(template_a)
        new_order = order.search([]) - preexisting
        self.assertEqual(len(new_order), 1)
        self.assertEqual(
            action["res_id"],
            new_order.id,
            msg="Returned action references the wrong record",
        )
        self.assertEqual(
            Counter(product_a1 + product_a2 + product_a3),
            Counter(new_order.stock_request_ids.mapped("product_id")),
            msg="Not all of the template's variants were ordered",
        )

        # Selecting a template
        preexisting = order.search([])
        action = order._create_from_product_multiselect(template_a + template_b)
        new_order = order.search([]) - preexisting
        self.assertEqual(len(new_order), 1)
        self.assertEqual(
            action["res_id"],
            new_order.id,
            msg="Returned action references the wrong record",
        )
        self.assertEqual(
            Counter(product_a1 + product_a2 + product_a3 + product_b1),
            Counter(new_order.stock_request_ids.mapped("product_id")),
            msg="Inactive variant was ordered though it shouldn't have been",
        )

        # If a user does not have stock request rights, they can still trigger
        # the action from the products, so test that they get a friendlier
        # error message.
        self.stock_request_user.groups_id -= self.stock_request_user_group
        with self.assertRaises(exceptions.AccessError):
            order.with_user(self.stock_request_user)._create_from_product_multiselect(
                template_a + template_b
            )

        # Empty recordsets should just return False
        self.assertFalse(
            order._create_from_product_multiselect(self.env["product.product"])
        )

        # Wrong model should just raise ValidationError
        with self.assertRaises(exceptions.ValidationError):
            order._create_from_product_multiselect(self.stock_request_user)

    def test_allow_virtual_location(self):
        self.main_company.stock_request_allow_virtual_loc = True
        vals = {
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_uom_qty": 5.0,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
        }
        stock_request = self.stock_request.with_user(self.stock_request_user).create(
            vals
        )
        self.assertTrue(stock_request.allow_virtual_location)
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
        }
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        self.assertTrue(order.allow_virtual_location)

    def test_onchange_wh_no_effect_from_order(self):
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
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
                        "location_id": self.virtual_loc.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        order.stock_request_ids.onchange_warehouse_id()
        self.assertEqual(order.stock_request_ids[0].location_id, self.virtual_loc)

    def test_cancellation(self):
        group = self.env["procurement.group"].create({"name": "Procurement group"})
        product2 = self._create_product("SH2", "Shoes2", False)
        product3 = self._create_product("SH3", "Shoes3", False)
        self.product.detailed_type = "consu"
        product2.detailed_type = "consu"
        product3.detailed_type = "consu"
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
            "procurement_group_id": group.id,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "procurement_group_id": group.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.virtual_loc.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": product2.id,
                        "product_uom_id": self.product.uom_id.id,
                        "procurement_group_id": group.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.virtual_loc.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": product3.id,
                        "product_uom_id": self.product.uom_id.id,
                        "procurement_group_id": group.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.virtual_loc.id,
                    },
                ),
            ],
        }
        order = self.request_order.create(vals)
        self.product.route_ids = [(6, 0, self.route.ids)]
        product2.route_ids = [(6, 0, self.route.ids)]
        product3.route_ids = [(6, 0, self.route.ids)]
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(1, len(picking))
        picking.action_assign()
        self.assertEqual(3, len(picking.move_ids))
        line = picking.move_ids.filtered(lambda r: r.product_id == self.product)
        line.quantity = 1
        line.picked = True
        sr1 = order.stock_request_ids.filtered(lambda r: r.product_id == self.product)
        sr2 = order.stock_request_ids.filtered(lambda r: r.product_id == product2)
        sr3 = order.stock_request_ids.filtered(lambda r: r.product_id == product3)
        self.assertNotEqual(sr1.state, "done")
        self.assertNotEqual(sr2.state, "done")
        self.assertNotEqual(sr3.state, "done")
        self.env["stock.backorder.confirmation"].with_context(
            button_validate_picking_ids=[picking.id]
        ).create({"pick_ids": [(4, picking.id)]}).process()
        sr1.invalidate_recordset()
        sr2.invalidate_recordset()
        sr3.invalidate_recordset()
        self.assertNotEqual(sr1.state, "done")
        self.assertNotEqual(sr2.state, "done")
        self.assertNotEqual(sr3.state, "done")
        picking = order.picking_ids.filtered(
            lambda r: r.state not in ["done", "cancel"]
        )
        self.assertEqual(1, len(picking))
        picking.action_assign()
        self.assertEqual(3, len(picking.move_ids))
        line = picking.move_ids.filtered(lambda r: r.product_id == self.product)
        line.quantity = 4
        line.picked = True
        line = picking.move_ids.filtered(lambda r: r.product_id == product2)
        line.quantity = 1
        line.picked = True
        self.env["stock.backorder.confirmation"].with_context(
            button_validate_picking_ids=[picking.id]
        ).create({"pick_ids": [(4, picking.id)]}).process_cancel_backorder()
        sr1.invalidate_recordset()
        sr2.invalidate_recordset()
        sr3.invalidate_recordset()
        self.assertEqual(sr1.state, "done")
        self.assertEqual(sr1.qty_done, 5)
        self.assertEqual(sr1.qty_cancelled, 0)
        self.assertEqual(sr2.state, "cancel")
        self.assertEqual(sr2.qty_done, 1)
        self.assertEqual(sr2.qty_cancelled, 4)
        self.assertEqual(sr3.state, "cancel")
        self.assertEqual(sr3.qty_done, 0)
        self.assertEqual(sr3.qty_cancelled, 5)
        # Set the request order to done if there are any delivered lines
        self.assertEqual(order.state, "done")


class TestStockRequestOrderState(TestStockRequest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a = cls._create_product(
            "CODEA",
            "Product A",
            cls.main_company.id,
        )
        cls.product_a.route_ids = [(6, 0, cls.route.ids)]
        cls.product_b = cls._create_product(
            "CODEB",
            "Product B",
            cls.main_company.id,
        )
        cls.product_b.route_ids = [(6, 0, cls.route.ids)]
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": cls.main_company.id,
            "warehouse_id": cls.warehouse.id,
            "location_id": cls.warehouse.lot_stock_id.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": cls.product_a.id,
                        "product_uom_id": cls.product_a.uom_id.id,
                        "product_uom_qty": 1.0,
                        "company_id": cls.main_company.id,
                        "warehouse_id": cls.warehouse.id,
                        "location_id": cls.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": cls.product_b.id,
                        "product_uom_id": cls.product_b.uom_id.id,
                        "product_uom_qty": 1.0,
                        "company_id": cls.main_company.id,
                        "warehouse_id": cls.warehouse.id,
                        "location_id": cls.warehouse.lot_stock_id.id,
                        "expected_date": expected_date,
                    },
                ),
            ],
        }
        cls.order = cls.request_order.create(vals)
        cls.request_a = cls.order.stock_request_ids.filtered(
            lambda x: x.product_id == cls.product_a
        )
        cls.request_b = cls.order.stock_request_ids.filtered(
            lambda x: x.product_id == cls.product_b
        )

    def test_stock_request_order_state_01(self):
        """Request A: Done + Request B: Done = Done."""
        self.order.action_confirm()
        self.request_a.action_done()
        self.request_b.action_done()
        self.assertEqual(self.request_a.state, "done")
        self.assertEqual(self.request_b.state, "done")
        self.assertEqual(self.order.state, "done")

    def test_stock_request_order_state_02(self):
        """Request A: Cancel + Request B: Cancel = Cancel."""
        self.order.action_confirm()
        self.request_a.action_cancel()
        self.request_b.action_cancel()
        self.assertEqual(self.request_a.state, "cancel")
        self.assertEqual(self.request_b.state, "cancel")
        self.assertEqual(self.order.state, "cancel")

    def test_stock_request_order_state_03(self):
        """Request A: Done + Request B: Cancel = Done."""
        self.order.action_confirm()
        self.request_a.action_done()
        self.request_b.action_cancel()
        self.assertEqual(self.request_a.state, "done")
        self.assertEqual(self.request_b.state, "cancel")
        self.assertEqual(self.order.state, "done")

    def test_stock_request_order_state_04(self):
        """Request A: Cancel + Request B: Done = DOne."""
        self.order.action_confirm()
        self.request_a.action_cancel()
        self.request_b.action_done()
        self.assertEqual(self.request_a.state, "cancel")
        self.assertEqual(self.request_b.state, "done")
        self.assertEqual(self.order.state, "done")

    def test_rounding_half_up_in_progress_01(self):
        product_half_up = self._create_product(
            "HALFUP", "HalfUp Product", self.main_company.id
        )
        product_half_up.uom_id.rounding = 1.0
        vals = {
            "product_id": product_half_up.id,
            "product_uom_id": product_half_up.uom_id.id,
            "product_uom_qty": 0.5,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
        }
        stock_request = self.stock_request.create(vals)
        stock_request.action_confirm()
        self.assertEqual(
            stock_request.qty_in_progress,
            1,
            "Quantity in progress should be the rounded up after confirmation",
        )

    def test_rounding_half_up_in_progress_02(self):
        product_half_up = self._create_product(
            "HALFUP", "HalfUp Product", self.main_company.id
        )
        product_half_up.uom_id.rounding = 1.0
        vals = {
            "product_id": product_half_up.id,
            "product_uom_id": product_half_up.uom_id.id,
            "product_uom_qty": 1.49,
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.virtual_loc.id,
        }
        stock_request = self.stock_request.create(vals)
        stock_request.action_confirm()
        self.assertEqual(
            stock_request.qty_in_progress,
            1,
            "Quantity in progress should be the rounded down after confirmation",
        )

    def test_route_id_propagation_on_creation(self):
        order_vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "route_id": self.route.id,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 10.0,
                    },
                ),
            ],
        }
        order = self.request_order.create(order_vals)
        self.assertEqual(len(order.stock_request_ids), 2)
        order.write({"route_id": self.route_3})
        for request in order.stock_request_ids:
            self.assertEqual(
                request.route_id.id,
                order.route_id.id,
                "The route_id from stock.request.order has not "
                "been set in the associated stock.requests.",
            )

    def test_compute_route_id_consistency_1(self):
        order_vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "route_id": self.route.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 10.0,
                        "route_id": self.route_3.id,
                    },
                ),
            ],
        }
        order = self.request_order.create(order_vals)
        order._compute_route_id()
        self.assertFalse(
            order.route_id,
            "Route ID should be False due to inconsistent routes in stock requests.",
        )

    def test_compute_route_id_consistency_2(self):
        order_vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "route_id": self.route.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 10.0,
                        "route_id": self.route.id,
                    },
                ),
            ],
        }
        order = self.request_order.create(order_vals)
        order._compute_route_id()
        self.assertEqual(order.route_id, self.route)

    def test_inverse_route_id_propagation(self):
        order_vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 10.0,
                    },
                ),
            ],
        }
        order = self.request_order.create(order_vals)
        order.route_id = self.route.id
        order._inverse_route_id()
        for request in order.stock_request_ids:
            self.assertEqual(
                request.route_id.id,
                self.route.id,
                "Route ID should propagate to all stock requests.",
            )

    def test_onchange_route_id_propagation(self):
        order_vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 5.0,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_id": self.product.uom_id.id,
                        "product_uom_qty": 10.0,
                    },
                ),
            ],
        }
        order = self.request_order.create(order_vals)
        order.route_id = self.route.id
        order._onchange_route_id()
        for request in order.stock_request_ids:
            self.assertEqual(
                request.route_id.id,
                self.route.id,
                "Route ID should update on all stock requests on onchange.",
            )


class TestStockRequestOrderChainedTransfers(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(
            context=dict(
                self.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        self.request_order = self.env["stock.request.order"]
        self.stock_request = self.env["stock.request"]
        self.main_company = self.env.ref("base.main_company")
        self.warehouse = self.env.ref("stock.warehouse0")
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.stock_request_user = new_test_user(
            self.env,
            login="stock_request_user",
            groups="stock_request.group_stock_request_user",
            company_ids=[(6, 0, [self.main_company.id])],
        )
        self.stock_request_manager = new_test_user(
            self.env,
            login="stock_request_manager",
            groups="stock_request.group_stock_request_manager",
            company_ids=[(6, 0, [self.main_company.id])],
        )
        self.product_test = self._create_product("PROD", "Product Test")
        self.stock_loc = self._create_location(
            name="Backstock",
            location_id=self.warehouse.view_location_id.id,
            company_id=self.main_company.id,
        )
        self.transit_loc = self._create_location(
            name="Transit",
            location_id=self.warehouse.view_location_id.id,
            company_id=self.main_company.id,
        )
        self.manufacturing_loc = self._create_location(
            name="Manufacturing",
            location_id=self.warehouse.view_location_id.id,
            company_id=self.main_company.id,
        )
        self.route = self.env["stock.route"].create(
            {
                "name": "Backstock to Manufacturing (2 steps)",
                "warehouse_selectable": True,
                "warehouse_ids": [(6, 0, [self.warehouse.id])],
                "rule_ids": [
                    (
                        0,
                        False,
                        {
                            "name": "Stock to Transit",
                            "location_src_id": self.stock_loc.id,
                            "location_dest_id": self.transit_loc.id,
                            "action": "pull",
                            "picking_type_id": self.warehouse.int_type_id.id,
                            "procure_method": "make_to_stock",
                            "warehouse_id": self.warehouse.id,
                            "company_id": self.main_company.id,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "name": "Transit to Manufacturing",
                            "location_src_id": self.transit_loc.id,
                            "location_dest_id": self.manufacturing_loc.id,
                            "action": "pull_push",
                            "picking_type_id": self.warehouse.int_type_id.id,
                            "procure_method": "make_to_order",
                            "warehouse_id": self.warehouse.id,
                            "company_id": self.main_company.id,
                        },
                    ),
                ],
            }
        )
        self.product_test.route_ids = [(6, 0, [self.route.id])]
        self._create_stock_quant(self.stock_loc, self.product_test, 5)

    def _create_product(self, default_code, name, **vals):
        return self.env["product.product"].create(
            dict(
                name=name,
                default_code=default_code,
                uom_id=self.uom_unit.id,
                uom_po_id=self.uom_dozen.id,
                type="product",
                **vals,
            )
        )

    def _create_location(self, **vals):
        return self.env["stock.location"].create(dict(usage="internal", **vals))

    def _create_stock_quant(self, location_id, product_id, qty):
        self.env["stock.quant"].create(
            {
                "location_id": location_id.id,
                "product_id": product_id.id,
                "quantity": qty,
            }
        )

    def test_two_pickings_related(self):
        """Test to check that order has two related pickings after confirmation"""
        expected_date = fields.Datetime.now()
        vals = {
            "company_id": self.main_company.id,
            "warehouse_id": self.warehouse.id,
            "location_id": self.manufacturing_loc.id,
            "expected_date": expected_date,
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product_test.id,
                        "product_uom_id": self.product_test.uom_id.id,
                        "product_uom_qty": 5.0,
                        "company_id": self.main_company.id,
                        "warehouse_id": self.warehouse.id,
                        "location_id": self.manufacturing_loc.id,
                        "expected_date": expected_date,
                    },
                )
            ],
        }
        order = self.request_order.with_user(self.stock_request_user).create(vals)
        order.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(len(order.mapped("picking_ids")), 2)
