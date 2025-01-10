from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class Test3WayMatch(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Vendor",
                "property_tax_exempt": True,
                "property_exemption_number": "12321",
                "property_exemption_code_id": cls.env.ref(
                    "account_avatax_oca.resale_type"
                ),
            }
        )
        cls.product_deliver = cls.env["product.product"].create(
            {
                "name": "Switch, 24 ports",
                "standard_price": 55.0,
                "list_price": 70.0,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "purchase_method": "receive",
                "default_code": "PROD_DEL",
                "taxes_id": False,
            }
        )

    def test_purchase_order_with_price_difference(self):
        purchase_order = (
            self.env["purchase.order"]
            .with_context(tracking_disable=True)
            .create({"partner_id": self.vendor.id, "override_po_exception": True})
        )

        PurchaseOrderLine = self.env["purchase.order.line"].with_context(
            tracking_disable=True
        )
        pol_prod_deliver = PurchaseOrderLine.create(
            {
                "name": self.product_deliver.name,
                "product_id": self.product_deliver.id,
                "product_qty": 10.0,
                "product_uom": self.product_deliver.uom_id.id,
                "price_unit": self.product_deliver.list_price,
                "order_id": purchase_order.id,
                "taxes_id": False,
            }
        )

        purchase_order.button_confirm()
        purchase_order.order_line.qty_received = 10
        action = purchase_order.action_create_invoice()
        vendor_bill = self.env["account.move"].browse(action["res_id"])
        move_line = vendor_bill.mapped("line_ids").filtered(
            lambda l: l.purchase_line_id
        )
        move_line.price_unit = 100
        self.assertEqual(move_line.po_line_price_difference, True)
        self.assertEqual(move_line.move_id.po_price_difference, True)

    def test_purchase_order_with_no_price_difference(self):
        purchase_order = (
            self.env["purchase.order"]
            .with_context(tracking_disable=True)
            .create({"partner_id": self.vendor.id, "override_po_exception": True})
        )

        PurchaseOrderLine = self.env["purchase.order.line"].with_context(
            tracking_disable=True
        )
        pol_prod_deliver = PurchaseOrderLine.create(
            {
                "name": self.product_deliver.name,
                "product_id": self.product_deliver.id,
                "product_qty": 10.0,
                "product_uom": self.product_deliver.uom_id.id,
                "price_unit": self.product_deliver.list_price,
                "order_id": purchase_order.id,
                "taxes_id": False,
            }
        )

        purchase_order.button_confirm()
        purchase_order.order_line.qty_received = 10
        action = purchase_order.action_create_invoice()
        vendor_bill = self.env["account.move"].browse(action["res_id"])
        move_line = vendor_bill.mapped("line_ids").filtered(
            lambda l: l.purchase_line_id
        )
        self.assertEqual(move_line.po_line_price_difference, False)
        self.assertEqual(move_line.move_id.po_price_difference, False)
