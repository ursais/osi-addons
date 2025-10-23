from odoo.tests import common, tagged
from odoo import fields
from datetime import date, timedelta

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestSaleBooking(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.product = cls.env.ref("product.product_product_6")
        cls.customer = cls.env["res.partner"].create({"name": "Vandan Pandeji"})
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor"})
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )
        cls.tomorrow = date.today() + timedelta(days=1)
        # Create a test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Demo",
                "categ_id": cls.env.ref("ol_base.product_category_components").id,
                "standard_price": 35.0,
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL01",
                "sale_delay": 0,
                "product_state_id": cls.env.ref(
                    "ol_product_state.product_state_active"
                ).id,
            }
        )

        vendor_pricelist = cls.env["product.supplierinfo"].create(
            {"partner_id": cls.vendor.id, "product_id": cls.product.id}
        )

    def test_sale_creation(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "pricelist_id": self.customer.property_product_pricelist.id,
                "original_commitment_date": "2025-06-12",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 500,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        sale_booking_id = self.env["sale.booking"].search(
            [("order_id", "=", sale_order.id)]
        )
        self.assertEqual(sale_order.name, sale_booking_id.origin)
        self.assertEqual(sale_order.company_id.id, sale_booking_id.company_id.id)
        self.assertEqual(sale_order.currency_id.id, sale_booking_id.currency_id.id)
        sale_order2 = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "pricelist_id": self.customer.property_product_pricelist.id,
                "original_commitment_date": "2025-06-12",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 500,
                        },
                    )
                ],
            }
        )
        sale_order2.action_cancel()

    def test_blanket_order_creation(self):
        blanket_order = self.env["sale.blanket.order"].create(
            {
                "partner_id": self.customer.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "original_uom_qty": 20.0,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 500,
                            "date_schedule": fields.Date.today(),
                        },
                    ),
                ],
            }
        )
        # Confirm the blanket order
        self.assertEqual(blanket_order.remaining_amount_untaxed, 10000.0)
        self.assertEqual(blanket_order.remaining_amount_tax, 0.0)
        self.assertEqual(blanket_order.remaining_amount_total, 10000.0)
        blanket_order.sudo().action_confirm()
