from odoo import Command
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestSaleMRPTags(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_obj = cls.env["res.partner"]
        cls.tag_obj = cls.env["crm.tag"]
        cls.product_obj = cls.env["product.product"]
        cls.sale_order_obj = cls.env["sale.order"]
        cls.mrp_bom_obj = cls.env["mrp.bom"]
        cls.partner = cls.partner_obj.create({"name": "Vandan Pandeji"})
        cls.manufacturing_route_id = cls.env.ref("mrp.route_warehouse0_manufacture")
        cls.route_warehouse0_mto_id = cls.env.ref("stock.route_warehouse0_mto")

        cls.tag_ids = cls.tag_obj.create(
            [{"name": "Sale MPR Tag 1"}, {"name": "Sale MPR Tag 2"},]
        )
        cls.product_A = cls.product_obj.create(
            {
                "name": "Table Top",
                "type": "product",
                "uom_id": 1,
                "route_ids": [
                    (4, cls.manufacturing_route_id.id),
                    (4, cls.route_warehouse0_mto_id.id),
                ],
            }
        )
        cls.product_B = cls.product_obj.create(
            {"name": "Wood Panel", "type": "product", "uom_id": 1,}
        )
        cls.tabel_top_bom = cls.mrp_bom_obj.create(
            {
                "product_tmpl_id": cls.product_A.product_tmpl_id.id,
                "product_qty": 1,
                "code": "BOM 1",
                "bom_line_ids": [
                    Command.create({"product_id": cls.product_B.id, "product_qty": 1,})
                ],
            }
        )

        cls.sale_order = cls.sale_order_obj.create(
            {
                "partner_id": cls.partner.id,
                "tag_ids": [(6, 0, cls.tag_ids.ids)],
                "order_line": [
                    Command.create(
                        {"product_id": cls.product_A.id, "product_uom_qty": 1.0,}
                    ),
                ],
            }
        )

    def test_check_tags(self):
        self.sale_order.action_confirm()
        mrp_order = self.env["mrp.production"].search(
            [("mrp_sale_id", "=", self.sale_order.id)]
        )
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.assertEqual(len(self.sale_order.tag_ids), len(mrp_order.tag_ids))
