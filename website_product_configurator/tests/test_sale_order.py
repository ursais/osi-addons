from ..tests.common import (
    TestProductConfiguratorValues,
)


class TestSaleOrder(TestProductConfiguratorValues):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.product = cls.env["product.product"].create({"name": "test product"})
        cls.product_uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "New Pricelist",
                "currency_id": cls.env.user.company_id.currency_id.id,
                "discount_policy": "without_discount",
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "name": "test SO",
                "partner_id": cls.partner.id,
                "partner_invoice_id": cls.partner.id,
                "partner_shipping_id": cls.partner.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": "Test Line",
                            "product_uom": cls.product_uom_unit.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 400.00,
                            "config_session_id": cls.session_id.id,
                        },
                    ),
                ],
            }
        )

    def test_cart_update(self):
        product_id = (
            self.sale_order.order_line.product_id.product_tmpl_id.product_variant_id.id
        )
        self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=0,
            add_qty=0,
        )
        self.assertFalse(
            self.product.product_tmpl_id.config_ok, "product is config_ok True"
        )
        self.product.product_tmpl_id.write({"config_ok": True})
        cart_update = self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=2,
            add_qty=2,
        )
        self.assertEqual(cart_update.get("line_id"), self.sale_order.order_line.id)
        self.assertEqual(
            cart_update.get("quantity"), self.sale_order.order_line.product_uom_qty
        )

        self.sale_order.write({"order_line": False})
        self.sale_order._cart_update(
            product_id=product_id,
            set_qty=1,
            add_qty=1,
        )
        self.assertTrue(self.sale_order.order_line, "No Sale Order Line created.")

        self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=-1,
            add_qty=1,
        )
        self.assertFalse(
            self.sale_order.order_line,
            "Order Line is exist for quantity is less than equal zero.",
        )

        self.sale_order._cart_update(
            line_id=self.sale_order.order_line.id,
            product_id=product_id,
            add_qty="test",
        )
        self.assertEqual(
            self.sale_order.order_line.product_uom_qty,
            1,
            "If wrong value is added then 1 quantity is deducted from Order Line.",
        )

        self.sale_order._cart_update(
            line_id=self.sale_order.order_line.id,
            product_id=product_id,
            set_qty="test",
        )
        self.assertEqual(
            self.sale_order.order_line.product_uom_qty,
            1,
            "If wrong value is added then Order Line quantity as it is.",
        )
