from odoo.tests import common


class TestRmaScrap(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.rma_obj = cls.env["rma.order"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_make_picking = cls.env["rma_make_picking.wizard"]
        cls.rma_make_scrap_wiz = cls.env["rma_make_scrap.wizard"]
        cls.product_obj = cls.env["product.product"]
        cls.partner_obj = cls.env["res.partner"]

        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")
        cls.cust_loc = cls.env.ref("stock.stock_location_customers")

        # Create customer
        cls.customer1 = cls.partner_obj.create({"name": "Customer 1"})

        # Create products
        cls.product_1 = cls.product_obj.create(
            {"name": "Test Product 1", "type": "product", "list_price": 100.0}
        )
        cls.product_2 = cls.product_obj.create(
            {
                "name": "Test Product 2",
                "type": "product",
                "list_price": 150.0,
                "tracking": "lot",
            }
        )

        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "Lot for tests",
                "product_id": cls.product_2.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.stock_rma_location = cls.wh.lot_rma_id
        cls.scrap_loc = cls.env["stock.location"].create(
            {
                "name": "WH Scrap Location",
                "location_id": cls.wh.view_location_id.id,
                "scrap_location": True,
            }
        )

        # Create RMA group and operation:
        cls.rma_group = cls.rma_obj.create({"partner_id": cls.customer1.id})

        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST1",
                "name": "Operation 1",
                "type": "customer",
                "receipt_policy": "ordered",
                "scrap_policy": "received",
                "scrap_location_id": cls.scrap_loc.id,
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )
        cls.operation_2 = cls.rma_op_obj.create(
            {
                "code": "TEST2",
                "name": "Operation 2",
                "type": "customer",
                "receipt_policy": "ordered",
                "scrap_policy": "ordered",
                "scrap_location_id": cls.scrap_loc.id,
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )

    def test_01_rma_scrap_received(self):
        rma = self.rma_line_obj.create(
            {
                "partner_id": self.customer1.id,
                "product_id": self.product_1.id,
                "operation_id": self.operation_1.id,
                "uom_id": self.product_1.uom_id.id,
                "in_route_id": self.operation_1.in_route_id.id,
                "out_route_id": self.operation_1.out_route_id.id,
                "in_warehouse_id": self.operation_1.in_warehouse_id.id,
                "out_warehouse_id": self.operation_1.out_warehouse_id.id,
                "location_id": self.stock_rma_location.id,
            }
        )
        rma._onchange_operation_id()
        rma.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})

        self.assertEqual(rma.qty_to_receive, 1.00)
        self.assertFalse(rma.qty_to_scrap)

        action_picking = wizard.action_create_picking()
        picking = self.env["stock.picking"].browse([action_picking["res_id"]])
        picking.move_line_ids[0].quantity = rma.qty_to_receive

        picking.button_validate()
        rma._compute_qty_to_scrap()

        self.assertFalse(rma.qty_to_receive)
        self.assertEqual(rma.qty_received, 1.00)
        self.assertEqual(rma.qty_to_scrap, 1.00)
        wizard = self.rma_make_scrap_wiz.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "item_ids": [
                    0,
                    0,
                    {
                        "line_id": rma.id,
                        "product_id": rma.product_id.id,
                        "product_qty": rma.product_qty,
                        "location_id": rma.location_id,
                        "qty_to_scrap": rma.qty_to_scrap,
                        "uom_id": rma.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_scrap()
        scrap = self.env["stock.scrap"].browse([action["res_id"]])
        self.assertEqual(scrap.location_id.id, self.stock_rma_location.id)
        self.assertEqual(scrap.move_ids.id, False)
        scrap.action_validate()
        move = scrap.move_ids
        self.assertEqual(move.product_id.id, self.product_1.id)
        self.assertFalse(rma.qty_to_scrap)
        self.assertEqual(rma.qty_scrap, 1.00)

    def test_02_rma_scrap_ordered(self):
        rma = self.rma_line_obj.create(
            {
                "partner_id": self.customer1.id,
                "product_id": self.product_1.id,
                "operation_id": self.operation_2.id,
                "uom_id": self.product_1.uom_id.id,
                "in_route_id": self.operation_2.in_route_id.id,
                "out_route_id": self.operation_2.out_route_id.id,
                "in_warehouse_id": self.operation_2.in_warehouse_id.id,
                "out_warehouse_id": self.operation_2.out_warehouse_id.id,
                "location_id": self.stock_rma_location.id,
            }
        )
        rma._onchange_operation_id()
        rma.action_rma_to_approve()
        rma._compute_qty_to_scrap()

        self.assertEqual(rma.qty_to_receive, 1.00)
        self.assertEqual(rma.qty_to_scrap, 1.00)
        self.assertFalse(rma.qty_in_scrap)

        wizard = self.rma_make_scrap_wiz.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "item_ids": [
                    0,
                    0,
                    {
                        "line_id": rma.id,
                        "product_id": rma.product_id.id,
                        "product_qty": rma.product_qty,
                        "location_id": rma.location_id,
                        "qty_to_scrap": rma.qty_to_scrap,
                        "uom_id": rma.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_scrap()
        scrap = self.env["stock.scrap"].browse([action["res_id"]])
        self.assertEqual(scrap.location_id.id, self.stock_rma_location.id)
        self.assertEqual(scrap.move_ids.id, False)
        self.assertEqual(rma.qty_in_scrap, 1.00)
        res = scrap.action_validate()
        scrap.do_scrap()
        self.assertTrue(res)
        self.assertEqual(rma.qty_scrap, 1.00)
