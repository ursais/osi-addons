from odoo.tests import common, tagged
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

    def test_partner_flow(self):
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
        self.assertEqual(sale_order.partner_id.open_so_balance, sale_order.amount_total)
        self.assertEqual(sale_order.partner_id.credit_hold, False)
