from odoo.tests import common, tagged
from odoo.exceptions import ValidationError

@tagged('-at_install', 'post_install')
class TestStockPicking(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
        })
        cls.stock_loc = cls.env.ref('stock.stock_location_stock')
        cls.customer_loc = cls.env.ref('stock.stock_location_customers')
        cls.out_type = cls.env.ref('stock.picking_type_out')

    def test_can_add_moves_outgoing(self):
        sale = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,  
            'price_unit': 100,
            'name': self.product.name,
        })

        picking = sale.picking_ids[:1] or self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.out_type.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'sale_id': sale.id,
        })

        user_yes = self.env['res.users'].create({
            'name': 'YesRights',
            'login': 'yes_out',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('stock.group_stock_user').id,
                self.env.ref('ol_stock.group_allow_add_delete_line_out').id,
            ])]
        })
        user_no = self.env['res.users'].create({
            'name': 'NoRights',
            'login': 'no_out',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        with self.assertRaises(ValidationError):
            self.env['stock.move'].with_user(user_no).create({
                'name': 'Unauthorized Move',
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 2,
                'picking_id': picking.id,
                'location_id': self.stock_loc.id,
                'location_dest_id': self.customer_loc.id,
            })

        self.env['stock.move'].with_user(user_yes).create({
            'name': 'Authorized Move',
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 2,
            'picking_id': picking.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
        })
