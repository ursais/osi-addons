from odoo.tests import common, tagged, Form
from odoo import exceptions

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestCreditLimit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.customer = cls.env.ref("hr.work_contact_mit")
        cls.product = cls.env.ref("product.product_product_6")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

    def test_check_partner_rollup_id(self):
        PartnerObj = self.env["res.partner"]
        rollup_partner_1 = PartnerObj.create(
            {"name": "RollUp Partner A", "is_company": False,}
        )

        rollup_partner_2 = PartnerObj.create(
            {"name": "RollUp Partner B", "is_company": False,}
        )
        rollup_partner_1.write(
            {"partner_rollup_id": rollup_partner_2.id,}
        )
        with self.assertRaises(exceptions.UserError):
            rollup_partner_2.write(
                {"partner_rollup_id": rollup_partner_1.id,}
            )
        partner_2 = PartnerObj.create(
            {"name": "RollUp Partner B", "is_company": False, "credit_limit": 0.0}
        )
        partner_2.onchange_credit_limit()

    def test_partner_flow(self):
        # Normal Flow
        PartnerObj = self.env["res.partner"]
        SaleOrderObj = self.env["sale.order"]
        compnay_a = PartnerObj.create(
            {"name": "Company A", "is_company": True, "credit_limit": 30,}
        )
        child_compnay_a = PartnerObj.create(
            {
                "name": "Child A",
                "is_company": False,
                "parent_id": compnay_a.id,
                "partner_rollup_id": compnay_a.id,
            }
        )
        self.assertEqual(compnay_a.remaining_credit, 30)
        self.assertEqual(child_compnay_a.remaining_credit, 30)
        self.customer.credit_limit = 400

        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 350,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.uom_unit.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        sale_order.action_confirm()
        self.assertEqual(sale_order.uninvoiced_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.open_so_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.credit_hold, False)
        self.assertEqual(
            sale_order.partner_id.remaining_credit,
            sale_order.partner_id.credit_limit - sale_order.amount_total,
        )
        pick = sale_order.picking_ids
        pick.move_ids.write({"quantity": 1, "picked": True})
        wiz_act = pick.action_assign()
        wiz_act = pick.button_validate()
        self.assertEqual(pick.credit_hold, False)

    def test_override_credit_limit_hold(self):
        PartnerObj = self.env["res.partner"]
        SaleOrderObj = self.env["sale.order"]
        self.customer.credit_limit = 400

        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 400,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "commitment_date": "2024-06-10",
                "pricelist_id": self.customer.property_product_pricelist.id,
                "override_credit_limit_hold": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.uom_unit.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        self.assertEqual(sale_order.uninvoiced_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.open_so_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.credit_hold, False)
        self.assertEqual(
            sale_order.partner_id.remaining_credit,
            sale_order.partner_id.credit_limit - sale_order.amount_total,
        )
        pick = sale_order.picking_ids
        pick.move_ids.write({"quantity": 1, "picked": True})
        wiz_act = pick.button_validate()
        self.assertEqual(pick.credit_hold, False)

    def test_sale_mrp_flow(self):
        route_manufacture = self.env.ref("mrp.route_warehouse0_manufacture").id
        route_mto = self.env.ref("purchase_stock.route_warehouse0_buy").id

        partner = self.env["res.partner"].create(
            {"name": "Customer", "credit_limit": 400}
        )

        bom_product = self.env["product.product"].create(
            {
                "name": "BOM Prodduct",
                "type": "product",
                "route_ids": [(4, route_mto), (4, route_manufacture)],
                "list_price": 350,
            }
        )

        bom_line = self.env["product.product"].create(
            {"name": "Line Product", "type": "product",}
        )

        bom = self.env["mrp.bom"].create(
            {
                "product_id": bom_product.id,
                "product_tmpl_id": bom_product.product_tmpl_id.id,
                "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [(5, 0), (0, 0, {"product_id": bom_line.id})],
            }
        )

        # order_form = Form(self.env['sale.order'])
        # order_form.partner_id = partner.id
        # order_form.commitment_date =  "2024-06-10",
        # order_form.pricelist_id= self.customer.property_product_pricelist.id,
        # with order_form.order_line.new() as line:
        #     line.product_id = bom_product.id
        #     line.product_uom = self.uom_unit.id
        #     line.product_uom_qty = 1
        # order = order_form.save()
        # order.action_confirm()
        # self.assertEqual(order.mrp_production_count, 1)
