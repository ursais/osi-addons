# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.fields import Datetime
from odoo.tests import common


class TestRmaPurchase(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.rma_obj = self.env["rma.order"]
        self.rma_line_obj = self.env["rma.order.line"]
        self.rma_op_obj = self.env["rma.operation"]
        self.rma_add_purchase_wiz = self.env["rma_add_purchase"]
        self.po_obj = self.env["purchase.order"]
        self.pol_obj = self.env["purchase.order.line"]
        self.product_obj = self.env["product.product"]
        self.partner_obj = self.env["res.partner"]

        self.rma_route_cust = self.env.ref("rma.route_rma_customer")

        # Create supplier
        supplier1 = self.partner_obj.create({"name": "Supplier 1"})

        # Create products
        self.product_1 = self.product_obj.create(
            {
                "name": "Test Product 1",
                "type": "product",
            }
        )
        self.product_2 = self.product_obj.create(
            {
                "name": "Test Product 2",
                "type": "product",
            }
        )

        # Create PO:
        self.po = self.po_obj.create(
            {
                "partner_id": supplier1.id,
            }
        )
        self.pol_1 = self.pol_obj.create(
            {
                "name": self.product_1.name,
                "order_id": self.po.id,
                "product_id": self.product_1.id,
                "product_qty": 20.0,
                "product_uom": self.product_1.uom_id.id,
                "price_unit": 100.0,
                "date_planned": Datetime.now(),
            }
        )
        self.pol_2 = self.pol_obj.create(
            {
                "name": self.product_2.name,
                "order_id": self.po.id,
                "product_id": self.product_2.id,
                "product_qty": 18.0,
                "product_uom": self.product_2.uom_id.id,
                "price_unit": 150.0,
                "date_planned": Datetime.now(),
            }
        )

        # Create RMA group:
        self.rma_group = self.rma_obj.create(
            {
                "partner_id": supplier1.id,
                "type": "supplier",
            }
        )

    def test_01_add_from_purchase_order(self):
        """Test wizard to create supplier RMA from Purchase Orders."""
        self.assertEqual(self.rma_group.origin_po_count, 0)
        add_purchase = self.rma_add_purchase_wiz.with_context(
            **{
                "supplier": True,
                "active_ids": self.rma_group.id,
                "active_model": "rma.order",
            }
        ).create(
            {
                "purchase_id": self.po.id,
                "purchase_line_ids": [(6, 0, self.po.order_line.ids)],
            }
        )
        add_purchase.add_lines()
        self.assertEqual(len(self.rma_group.rma_line_ids), 2)
        for t in self.rma_group.rma_line_ids.mapped("type"):
            self.assertEqual(t, "supplier")
        self.assertEqual(self.rma_group.origin_po_count, 1)

    def test_02_fill_rma_from_po_line(self):
        """Test filling a RMA (line) from a Purchase Order line."""
        rma = self.rma_line_obj.new(
            {
                "partner_id": self.po.partner_id.id,
                "purchase_order_line_id": self.pol_1.id,
                "type": "supplier",
            }
        )
        self.assertFalse(rma.product_id)
        rma._onchange_purchase_order_line_id()
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_qty, 20.0)
