from odoo import Command
from odoo.tests import common


class TestSaleStockTags(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_obj = cls.env["res.partner"]
        cls.tag_obj = cls.env["crm.tag"]
        cls.product_obj = cls.env["product.product"]
        cls.sale_order_obj = cls.env["sale.order"]
        cls.partner = cls.partner_obj.create({"name": "A Customer"})
        cls.tag_ids = cls.tag_obj.create(
            [
                {"name": "Tag_test_1"},
                {"name": "Tag_test_2"},
            ]
        )
        cls.product_A = cls.product_obj.create(
            {
                "name": "Product A",
                "type": "product",
                "uom_id": 1,
            }
        )
        cls.sale_order = cls.sale_order_obj.create(
            {
                "partner_id": cls.partner.id,
                "tag_ids": [(6, 0, cls.tag_ids.ids)],
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product_A.id,
                            "product_uom_qty": 5.0,
                        }
                    ),
                ],
            }
        )

    def test_check_tags(self):
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids)
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.assertEqual(
            len(self.sale_order.tag_ids), len(self.sale_order.picking_ids.tag_ids)
        )
