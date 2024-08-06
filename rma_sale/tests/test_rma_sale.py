# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaSale(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.rma_obj = cls.env["rma.order"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_add_sale_wiz = cls.env["rma_add_sale"]
        cls.rma_make_sale_wiz = cls.env["rma.order.line.make.sale.order"]
        cls.so_obj = cls.env["sale.order"]
        cls.sol_obj = cls.env["sale.order.line"]
        cls.product_obj = cls.env["product.product"]
        cls.partner_obj = cls.env["res.partner"]

        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")

        # Create customer
        customer1 = cls.partner_obj.create({"name": "Customer 1"})

        # Create products
        cls.product_1 = cls.product_obj.create(
            {"name": "Test Product 1", "type": "product", "list_price": 100.0}
        )
        cls.product_2 = cls.product_obj.create(
            {"name": "Test Product 2", "type": "product", "list_price": 150.0}
        )

        # Create SO:
        cls.so = cls.so_obj.create(
            {
                "partner_id": customer1.id,
                "partner_invoice_id": customer1.id,
                "partner_shipping_id": customer1.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product_1.name,
                            "product_id": cls.product_1.id,
                            "product_uom_qty": 20.0,
                            "product_uom": cls.product_1.uom_id.id,
                            "price_unit": cls.product_1.list_price,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.product_2.name,
                            "product_id": cls.product_2.id,
                            "product_uom_qty": 18.0,
                            "product_uom": cls.product_2.uom_id.id,
                            "price_unit": cls.product_2.list_price,
                        },
                    ),
                ],
            }
        )

        # Create RMA group and operation:
        cls.rma_group = cls.rma_obj.create({"partner_id": customer1.id})
        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Sale afer receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "sale_policy": "received",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )
        cls.operation_2 = cls.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Receive and Sale",
                "type": "customer",
                "receipt_policy": "ordered",
                "sale_policy": "ordered",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )

    def test_01_add_from_sale_order(self):
        """Test wizard to create RMA from Sales Orders."""
        add_sale = self.rma_add_sale_wiz.with_context(
            **{
                "customer": True,
                "active_ids": self.rma_group.id,
                "active_model": "rma.order",
            }
        ).create(
            {"sale_id": self.so.id, "sale_line_ids": [(6, 0, self.so.order_line.ids)]}
        )
        add_sale.add_lines()
        self.assertEqual(len(self.rma_group.rma_line_ids), 2)

    def test_02_rma_sale_operation(self):
        """Test RMA quantities using sale operations."""
        # Received sale_policy:
        rma_1 = self.rma_group.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        rma_1.write({"operation_id": self.operation_1.id})
        rma_1._onchange_operation_id()
        self.assertEqual(rma_1.sale_policy, "received")
        self.assertEqual(rma_1.qty_to_sell, 0.0)
        # TODO: receive and check qty_to_sell is 20.0
        # Ordered sale_policy:
        rma_2 = self.rma_group.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        rma_2.write({"operation_id": self.operation_2.id})
        rma_2._onchange_operation_id()
        self.assertEqual(rma_2.sale_policy, "ordered")
        self.assertEqual(rma_2.qty_to_sell, 18.0)

    def test_03_rma_create_sale(self):
        """Generate a Sales Order from a customer RMA."""
        rma = self.rma_group.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        self.assertEqual(rma.sales_count, 0)
        self.assertEqual(rma.qty_to_sell, 18.0)
        self.assertEqual(rma.qty_sold, 0.0)
        make_sale = self.rma_make_sale_wiz.with_context(
            **{"customer": True, "active_ids": rma.id, "active_model": "rma.order.line"}
        ).create({"partner_id": rma.partner_id.id})
        make_sale.make_sale_order()
        self.assertEqual(rma.sales_count, 1)
        rma.sale_line_ids.order_id.action_confirm()
        self.assertEqual(rma.qty_to_sell, 0.0)
        self.assertEqual(rma.qty_sold, 18.0)

    def test_04_fill_rma_from_so_line(self):
        """Test filling a RMA (line) from a Sales Order line."""
        so_line = self.so.order_line.filtered(lambda r: r.product_id == self.product_1)
        rma = self.rma_line_obj.new(
            {"partner_id": self.so.partner_id.id, "sale_line_id": so_line.id}
        )
        self.assertFalse(rma.product_id)
        rma._onchange_sale_line_id()
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_qty, 20.0)
