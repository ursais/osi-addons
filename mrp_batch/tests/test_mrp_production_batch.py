from odoo.tests import common
from odoo.fields import Command

class TestModule(common.TransactionCase):
    def setUp(self):
        super(TestModule, self).setUp()
    
    def test_sale_order_batch_with_allowe_split_mo(self):
     
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        mto_route = warehouse.mto_pull_id.route_id.id
        manufacture_route = warehouse.manufacture_pull_id.route_id.id
        free_product = self.env['product.product'].create({
           'name':'laptop',
           'detailed_type':'product',
           'tracking':'serial',
           'is_allowe_split_mo':True,
           'route_ids': [(6, 0, [mto_route,manufacture_route])],
        })
        self.assertEqual(free_product.is_allowe_split_mo,True)
        partner = self.env['res.partner'].create({'name':'Jone'})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Dummy section',
                }),
                Command.create({
                    'product_id': free_product.id,
                    'product_uom_qty':10
                }),  
            ]
        })
        sale_order = order.action_confirm()

    def test_sale_order_batch_without_allowe_split_mo(self):
     
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        mto_route = warehouse.mto_pull_id.route_id.id
        manufacture_route = warehouse.manufacture_pull_id.route_id.id
        free_product = self.env['product.product'].create({
           'name':'laptop',
           'detailed_type':'product',
           'tracking':'serial',
           'is_allowe_split_mo': False,
           'route_ids': [(6, 0, [mto_route,manufacture_route])],
        })
        self.assertEqual(free_product.is_allowe_split_mo,False)
        partner = self.env['res.partner'].create({'name':'Jone'})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Dummy section',
                }),
                Command.create({
                    'product_id': free_product.id,
                    'product_uom_qty':10
                }),  
            ]
        })
        sale_order = order.action_confirm()

    def test_manufacture_order_batch(self):

        product = self.env['product.product'].create({
           'name':'Book',
        })
        tag_ids = self.env['mrp.production.batch.tag'].create([{'name':'Test 1'},{'name':'Test 2'}])
        user_id = self.env['res.users'].create({'name':'Jone','login':'jone123@gmail.com'})
        manufacture_order_ids = self.env['mrp.production'].create([
            {'product_id': product.id},
            {'product_id': product.id},
            {'product_id': product.id},
            {'product_id': product.id}
            ])    
        wizard_id = self.env['mrp.production.batch.wizard'].create({'responsible_id':user_id.id,'tag_ids':tag_ids.ids})
        batch_id = self.env['mrp.production.batch'].create({"responsible_id":wizard_id.responsible_id.id,'tag_ids':wizard_id.tag_ids.ids ,"production_ids":manufacture_order_ids.ids})
        self.assertEqual(len(batch_id.tag_ids),2)
        self.assertEqual(manufacture_order_ids,batch_id.production_ids)
        batch_id.production_ids[0].action_remove_batch()
        self.assertEqual(len(batch_id.production_ids.ids),3)
        order_confirm = batch_id.action_confirm()
        order_cancel = batch_id.action_cancel()
        order_done = batch_id.action_done()
        
        
        
