from odoo.tests import common, tagged
from odoo.exceptions import ValidationError

@tagged('-at_install', 'post_install')
class TestStockMove(common.TransactionCase):

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
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2,
                'price_unit': 100,
            })]
        })
        cls.picking = cls.sale_order.picking_ids[:1] or cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
        })
        if not cls.picking.move_ids:
            cls.env['stock.move'].create({
                'name': cls.product.name,
                'product_id': cls.product.id,
                'product_uom': cls.product.uom_id.id,
                'product_uom_qty': 2,
                'picking_id': cls.picking.id,
                'location_id': cls.env.ref('stock.stock_location_stock').id,
                'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            })

    def test_stock_move_rules(self):
        move = self.picking.move_ids[0]

        user_no_rights = self.env['res.users'].create({
            'name': 'NoRights',
            'login': 'norights_test_stock_move',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        with self.assertRaises(ValidationError):
            move.with_user(user_no_rights).unlink()

        user_with_rights = self.env['res.users'].create({
            'name': 'HasRights',
            'login': 'hasrights_test_stock_move',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('ol_stock.group_allow_add_delete_line_out').id
            ])]
        })

        move_copy = move.copy({'picking_id': self.picking.id})
        move_copy.with_user(user_with_rights).unlink()

        picking_in = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'sale_id': self.sale_order.id,
        })
        move_in = self.env['stock.move'].create({
            'name': 'Incoming Move',
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 6,
            'picking_id': picking_in.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'sale_id': self.sale_order.id,
        })

        with self.assertRaises(ValidationError):
            move_in._check_quantity()

        move_in.product_uom_qty = 5
        move_in._check_quantity()
