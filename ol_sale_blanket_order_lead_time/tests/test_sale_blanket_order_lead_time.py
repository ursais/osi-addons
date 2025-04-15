from datetime import date, timedelta
from odoo import fields
from odoo.tests import common


class TestSaleBlanketOrderLeadTime(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        # Set up the test environment, create necessary objects and data for testing
        super().setUpClass()
        cls.blanket_order_obj = cls.env["sale.blanket.order"]
        cls.res_partner_obj = cls.env["res.partner"]
        cls.so_obj = cls.env["sale.order"]

        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )
        cls.test_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )

        # Create a custom unit of measure (UoM) for testing
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")
        cls.uom_dozen = cls.env["uom.uom"].create(
            {
                "name": "Test-DozenA",
                "category_id": cls.categ_unit.id,
                "factor_inv": 12,
                "uom_type": "bigger",
                "rounding": 0.001,
            }
        )

        # Create a test customer (partner)
        cls.partner = cls.res_partner_obj.create(
            {
                "name": "TEST CUSTOMER",
                "property_product_pricelist": cls.sale_pricelist.id,
            }
        )
        cls.partner_invoice_id = cls.res_partner_obj.create({
            'name': 'Partner Invoice Address',
            'parent_id': cls.partner.id,
            'type': 'invoice',
        })
        cls.partner_shipping_id = cls.res_partner_obj.create({
            'name': 'Partner Delivery Address',
            'parent_id': cls.partner.id,
            'type': 'delivery',
        })
        cls.vendor = cls.res_partner_obj.create({
            'name': 'AAA',
            'email': 'from.test@example.com',
        })

        # Create a test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Demo",
                "categ_id": cls.env.ref("product.product_category_1").id,
                "standard_price": 35.0,
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL01",
                "sale_delay": 0,
                "seller_ids": [(0, 0, {'partner_id': cls.vendor.id, 'product_code': 'COMP1', 'delay': 22})],
            }
        )
        cls.product_component = cls.env['product.product'].create({
            'name': 'Botox',
            'type': 'product',
            'uom_id': cls.env.ref("uom.product_uom_unit").id,
            'uom_po_id': cls.env.ref("uom.product_uom_unit").id,
            "seller_ids": [(0, 0, {'partner_id': cls.vendor.id, 'product_code': 'COMP1', 'delay': 11})],
        })

        # Calculate tomorrow's date
        cls.tomorrow = date.today() + timedelta(days=1)

    def test_01_create_blanket_order_lead_time_with_so(self):
        """Test creating a blanket order with associated sale orders."""
        # Create a blanket order with one line item
        self.product.sale_ok = True
        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.partner.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 20.0,
                            "price_unit": 30.0,
                            "date_schedule": fields.Date.today(),
                        },
                    ),
                ],
            }
        )

        blanket_order.action_compute_esd()
        self.assertEqual(sum(blanket_order.line_ids.mapped("customer_lead")), sum(blanket_order.line_ids.mapped("product_id.seller_ids.delay")))

        # Trigger onchange for partner to update related fields
        blanket_order.sudo().onchange_partner_id()

        # Confirm the blanket order
        blanket_order.sudo().action_confirm()

        # Check that the blanket order has one line item
        self.assertEqual(len(blanket_order.line_ids), 1)

        # Run the cron job to create sale orders from the blanket order
        self.blanket_order_obj.create_sale_order_cron()

        # Check that the blanket order is in the 'done' state
        self.assertEqual(blanket_order.state, "done")

        # View the sale orders created from the blanket order
        view_action = blanket_order.action_view_sale_orders()
        domain_ids = view_action["domain"][0][2]

        # Check that one sale order was created
        self.assertEqual(len(domain_ids), 1)

        # Browse the created sale order
        sale_order = self.so_obj.browse(domain_ids)
        self.assertEqual(sale_order.partner_invoice_id, self.partner_invoice_id)
        self.assertEqual(sale_order.partner_shipping_id, self.partner_shipping_id)

        # Check that the origin of the sale order matches the blanket order name
        self.assertEqual(sale_order.origin, blanket_order.name)

        # Get the sale order IDs linked to the blanket order lines
        so = blanket_order.mapped("line_ids.sale_lines.order_id.id")

        # Check that the created sale order ID is in the list
        self.assertIn(sale_order.id, so)

    def test_02_blanket_order_with_bom(self):
        bom_id = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_id": self.product.id,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
                'consumption': 'flexible',
                'bom_line_ids': [(0, 0, {
                    'product_id': self.product_component.id,
                    'product_qty': 10,
                    'product_uom_id': self.env.ref("uom.product_uom_unit").id,
                })]
            }
        )
        def create_order(product_id, partner_id, date_order):
            f = common.Form(self.env['purchase.order'])
            f.partner_id = partner_id
            f.date_order = date_order
            with f.order_line.new() as line:
                line.product_id = product_id
                line.product_qty = 1.0
                line.price_unit = 30
            return f.save()
        po_today = create_order(self.product_component, self.partner, fields.Datetime.now())
        po_today.button_confirm()

        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.partner.id,
                "validity_date": fields.Date.to_string(self.tomorrow),
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "auto_release": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 20.0,
                            "price_unit": 30.0,
                            "date_schedule": fields.Date.today(),
                            "bom_id": bom_id.id
                        },
                    ),
                ],
            }
        )
        blanket_order.action_compute_esd()
        product_delay = sum(blanket_order.line_ids.mapped("product_id.seller_ids.delay"))
        component_delay = sum(blanket_order.line_ids.mapped("bom_id.bom_line_ids.product_id.seller_ids.delay"))
        self.assertTrue(blanket_order.line_ids.mapped("bom_id"))
        self.assertEqual(blanket_order.line_ids.mapped("customer_lead")[0], product_delay + component_delay)
