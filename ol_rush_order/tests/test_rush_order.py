from odoo.tests import common
from odoo.fields import Command


class TestModule(common.TransactionCase):
    def setUp(self):
        super(TestModule, self).setUp()

    def test_sale_rush_order_true(self):
        free_product = self.env["product.product"].create(
            {
                "name": "laptop",
                "triggers_rush": True,
            }
        )
        self.assertEqual(free_product.triggers_rush, True)
        partner = self.env["res.partner"].create({"name": "Jone"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Dummy section",
                        }
                    ),
                    Command.create(
                        {
                            "product_id": free_product.id,
                        }
                    ),
                ],
            }
        )
        order._onchange_rush_order()
        self.assertEqual(order.rush_order, True)
        sale_order = order.action_confirm()

    def test_sale_rush_order_false(self):
        free_product = self.env["product.product"].create(
            {
                "name": "laptop1",
                "triggers_rush": False,
            }
        )
        self.assertEqual(free_product.triggers_rush, False)
        partner = self.env["res.partner"].create({"name": "Jone"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Dummy section",
                        }
                    ),
                    Command.create(
                        {
                            "product_id": free_product.id,
                        }
                    ),
                ],
            }
        )
        order._onchange_rush_order()
        self.assertEqual(order.rush_order, False)
        sale_order = order.action_confirm()
