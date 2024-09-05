# Copyright 2017-2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields
from odoo.tests import common, new_test_user

from ..hooks import uninstall_hook


class TestStockRequestSubmit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_company = cls.env.ref("base.main_company")
        cls.company_2 = cls.env["res.company"].create(
            {"name": "Company2", "parent_id": cls.main_company.id}
        )
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.route = cls.env["stock.route"].create(
            dict(
                name="Transfer",
                company_id=cls.main_company.id,
                product_categ_selectable=False,
                product_selectable=True,
                sequence=10,
            )
        )
        cls.ressuply_loc = cls.env["stock.location"].create(
            dict(
                name="Ressuply",
                location_id=cls.warehouse.view_location_id.id,
                company_id=cls.main_company.id,
            )
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
        cls.product = cls.env["product.product"].create(
            dict(
                name="Shoes",
                default_code="SH",
                uom_id=cls.env.ref("uom.product_uom_unit").id,
                company_id=False,
                detailed_type="product",
            )
        )
        cls.product.route_ids = [(6, 0, cls.route.ids)]
        vals = {
            "company_id": cls.main_company.id,
            "warehouse_id": cls.warehouse.id,
            "location_id": cls.warehouse.lot_stock_id.id,
            "expected_date": fields.Datetime.now(),
            "stock_request_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": cls.product.id,
                        "product_uom_id": cls.product.uom_id.id,
                        "product_uom_qty": 5.0,
                        "company_id": cls.main_company.id,
                        "warehouse_id": cls.warehouse.id,
                        "location_id": cls.warehouse.lot_stock_id.id,
                        "expected_date": fields.Datetime.now(),
                    },
                )
            ],
        }
        cls.request_order = cls.env["stock.request.order"]
        cls.stock_request_user = new_test_user(
            cls.env,
            login="stock_request_user2",
            groups="stock_request.group_stock_request_user",
            company_ids=[(6, 0, [cls.main_company.id, cls.company_2.id])],
        )
        cls.stock_request_manager = new_test_user(
            cls.env,
            login="stock_request_manager",
            groups="stock_request.group_stock_request_manager",
            company_ids=[(6, 0, [cls.main_company.id, cls.company_2.id])],
        )
        cls.order = cls.request_order.with_user(cls.stock_request_user).create(vals)
        cls.stock_request = cls.order.stock_request_ids

    def test_stock_request_submit(self):
        self.order.action_submit()
        self.assertEqual(self.order.state, "submitted")
        self.assertEqual(self.stock_request.state, "submitted")
        self.order.with_user(self.stock_request_manager).action_confirm()
        self.assertEqual(self.order.state, "open")
        self.assertEqual(self.stock_request.state, "open")

    def test_uninstall_hook(self):
        # Check state before uninstall
        self.order.action_submit()
        self.assertEqual(self.order.state, "submitted")
        self.assertEqual(self.stock_request.state, "submitted")

        # Uninstall this module
        uninstall_hook(self.env)

        # Check state after uninstall
        self.assertEqual(self.order.state, "draft")
        self.assertEqual(self.stock_request.state, "draft")
