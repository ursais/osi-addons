# Copyright 2018 Open Source Integrators
#   (http://www.opensourceintegrators.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from odoo.tests import common


class TestDefaultPurchaseSupplier(common.TransactionCase):

    def setUp(self):
        super(TestDefaultPurchaseSupplier, self).setUp()

        # Refs
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_uom = self.env.ref('product.product_uom_unit')

        # Get required Model
        self.product_model = self.env['product.product']
        self.product_ctg_model = self.env['product.category']
        self.purchase_model = self.env['purchase.order']
        # self.mail_model = self.env['mail.mail']

        # Create Product category and Products
        self.product_ctg = self._create_product_category()
        # self.generic_product = self.env.ref(
        #    'osi_default_purchase_supplier.product_template_generic_product')
        self.test_product = self._create_test_product()

        # Prepare purchase order values
        self.po_vals = {
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.test_product.name,
                    'product_id': self.test_product.id,
                    'product_qty': 5.0,
                    'product_uom': self.test_product.uom_po_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DF),
                })],
        }

    def _create_product_category(self):
        """Create a Product Category."""
        return self.product_ctg_model.create({'name': 'Product Catg'})

    def _create_test_product(self):
        """Create a Test Product."""
        product = self.product_model.create({
            'name': 'Test Product',
            'categ_id': self.product_ctg.id,
            'type': 'product',
            'uom_id': self.product_uom.id,
        })
        return product

    def test_default_purchase_supplier(self):
        """Test Default Purchase Supplier functionality"""

        # Create purchase order with purchase user access rights
        self.po = self.purchase_model.create(self.po_vals)
        self.assertTrue(self.po, 'Purchase: no purchase order created')
        self.assertEqual(self.po.state, 'draft')
        # Confirm purchase order
        self.po.button_confirm()
        # It should be still on draft state because it holds generic product
        # self.assertEqual(self.po.state, 'draft')
        # Update flag to send email for final varification
        # self.po.final_verification_flag = True
        # Check email send to purchase order creator
        # po_mail = self.mail_model.search([
        #    ('res_id', '=', self.po.id),
        #    ('model', '=', 'purchase.order')
        # ])
        # self.assertNotEqual(po_mail.ids, 0, 'No mail send.')
        # self.po.button_confirm()
        self.final_verification_flag = False
        self.assertEqual(self.po.state, 'purchase')
        self.assertEqual(self.po.picking_count, 1,
                         'Purchase: one picking should be created"')
        self.picking = self.po.picking_ids[0]
        # Cancel picking and delete it
        self.picking.action_cancel()
        self.picking.unlink()
        # Cancel purchase order and delete it
        self.po.button_cancel()
        self.po.unlink()
