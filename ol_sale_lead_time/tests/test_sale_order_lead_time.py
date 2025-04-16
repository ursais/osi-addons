from odoo import fields
from odoo.tests import common


class TestSaleOrderLeadTime(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        # Set up the test environment, create necessary objects and data for testing
        super().setUpClass()
        cls.res_partner_obj = cls.env["res.partner"]
        cls.so_obj = cls.env["sale.order"]
        cls.sale_pricelist = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": cls.env.ref("base.USD").id}
        )
        # Create a test customer (partner)
        cls.partner = cls.create_partner(
            cls,
            parent_id=False,
            name='TEST CUSTOMER',
        )
        cls.partner.property_product_pricelist = cls.sale_pricelist.id
        cls.partner_invoice_id = cls.create_partner(
            cls,
            parent_id=cls.partner.id,
            name='Partner Invoice Address',
            address_type='invoice'
        )
        cls.partner_shipping_id = cls.create_partner(
            cls,
            parent_id=cls.partner.id,
            name='Partner Delivery Address',
            address_type='delivery'
        )
        cls.vendor = cls.create_partner(
            cls,
            parent_id=False,
            name='TEST VENDOR',
        )

        # Create a test product
        cls.product = cls.create_product(
            cls,
            name="TOM",
            default_code="PROD_DEL01",
            seller_delay=22
        )
        cls.product_component = cls.create_product(
            cls,
            name="Botox",
            default_code="BTX01",
            seller_delay=11
        )

    def create_partner(self, parent_id, name, address_type="contact"):
        return self.res_partner_obj.create({
            'name': name,
            'parent_id': parent_id,
            'type': address_type,
        })

    def create_product(cls, name, product_type='product', default_code=None, seller_delay=0):
        """Helper method to create a product."""
        product_data = {
            "name": name,
            "categ_id": cls.env.ref("product.product_category_1").id,
            "standard_price": 30,
            "type": product_type,
            "uom_id": cls.env.ref("uom.product_uom_unit").id,
            "default_code": default_code,
            "seller_ids": [(0, 0, {
                'partner_id': cls.vendor.id,
                'product_code': 'COMP1',
                'delay': seller_delay
            })]
        }
        return cls.env["product.product"].create(product_data)

    def create_sale_order(self, partner_id, invoice_id, shipping_id, pricelist_id, product, quantity, bom_id=False):
        """Helper method to create a sale order."""
        return self.env['sale.order'].create({
            'partner_id': partner_id,
            'partner_invoice_id': invoice_id,
            'partner_shipping_id': shipping_id,
            'pricelist_id': pricelist_id,
            'order_line': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'product_uom_qty': quantity,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
                "bom_id": bom_id,
            })],
        })


    def test_01_create_sale_order_lead_time(self):
        # Create a sale order with the test product
        sale_order = self.create_sale_order(
            partner_id=self.partner.id,
            invoice_id=self.partner_invoice_id.id,
            shipping_id=self.partner_shipping_id.id,
            pricelist_id=self.sale_pricelist.id,
            product=self.product,
            quantity=10,
        )
        sale_order.action_compute_esd()
        self.assertEqual(sum(sale_order.order_line.mapped("customer_lead")), sum(sale_order.order_line.mapped("product_id.seller_ids.delay")))

    def test_02_sale_order_with_bom(self):
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

        sale_order = self.create_sale_order(
            partner_id=self.partner.id,
            invoice_id=self.partner_invoice_id.id,
            shipping_id=self.partner_shipping_id.id,
            pricelist_id=self.sale_pricelist.id,
            product=self.product,
            quantity=10,
            bom_id=bom_id.id,
        )
        sale_order.action_compute_esd()
        product_delay = sum(sale_order.order_line.mapped("product_id.seller_ids.delay"))
        component_delay = sum(sale_order.order_line.mapped("bom_id.bom_line_ids.product_id.seller_ids.delay"))
        self.assertTrue(sale_order.order_line.mapped("bom_id"))
        self.assertEqual(sale_order.order_line.mapped("customer_lead")[0], product_delay + component_delay)
