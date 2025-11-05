from odoo.tests import common, tagged
from datetime import date, datetime
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT

@tagged('-at_install', 'post_install')
class TestStockPicking(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.partner = cls.env.ref('base.res_partner_2')
        cls.payment_method_id = cls.env["payment.method"].search([], limit=1)
        cls.sale_order_obj = cls.env['sale.order']

        cls.user_no_rights = cls.env.ref("base.user_demo",False)

        cls.product = cls.env['product.product'].create([
            {
                'name': 'Onlogic Product',
                'type': 'product',
                'uom_id': cls.env.ref('uom.product_uom_unit').id,
                'categ_id':cls.env.ref('ol_base.product_category_components_accessories').id,
                'product_state_id': cls.env.ref("ol_product_state.product_state_active").id,
                'invoice_policy':"order",
            }
        ])
        # Create a Sale Order
        cls.sale_order = cls.sale_order_obj.create({
            'partner_id': cls.partner.id,
            'commitment_date': fields.Datetime.to_string(datetime.now()),
            "sale_payment_method_id": cls.payment_method_id.id,
            'picking_policy': 'direct',
        })
        if "override_saleable_exception" in cls.sale_order_obj.fields_get():
            cls.sale_order.write({'override_saleable_exception': True})

        # Create a Sale Order Line
        cls.sale_order_line = cls.env['sale.order.line'].create({
            'product_id': cls.product.id,
            'price_unit': 10,
            'product_uom_qty': 1,
            'product_uom':cls.product.uom_id.id,
            'order_id': cls.sale_order.id,
        })

        cls.picking_out = cls.env['stock.picking'].sudo().create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            'sale_id': cls.sale_order.id
        })
        cls.stock_move = cls.env['stock.move'].sudo().create({
            'name': cls.product.name,
            'product_id': cls.product.id,
            'product_uom': cls.product.uom_id.id,
            'product_uom_qty': 1,
            'picking_id': cls.picking_out.id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            'sale_line_id': cls.sale_order.order_line[0].id,
            'note': 'Initial note'
        })

    def test01_sale_confirm_do_unlink(self):
        # Confirm Sale Order and validate delivery
        sale_order = self.sale_order
        sale_order_line = self.sale_order_line
        sale_order.action_confirm()

        self.picking_out.write({"sale_id":self.sale_order.id})
        self.picking_out._compute_can_add_stock_moves()
        with self.assertRaises(ValidationError):
            self.picking_out.move_ids.with_user(self.user_no_rights).unlink()
