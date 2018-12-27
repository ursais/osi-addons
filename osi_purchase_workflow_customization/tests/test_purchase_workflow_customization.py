# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from odoo.tests import common
from odoo import SUPERUSER_ID


class TestPurchaseWorkflowCustomization(common.TransactionCase):

    def setUp(self):
        super(TestPurchaseWorkflowCustomization, self).setUp()

        # Refs
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_uom = self.env.ref('product.product_uom_unit')
        self.employee_fpi = self.env.ref('hr.employee_fpi')
        self.employee_mit = self.env.ref('hr.employee_mit')
        self.group_purchase_manager = self.env.ref(
            'purchase.group_purchase_manager')
        self.group_purchase_user = self.env.ref('purchase.group_purchase_user')
        self.company1 = self.env.ref('base.main_company')

        # Get required Model
        self.product_model = self.env['product.product']
        self.product_ctg_model = self.env['product.category']
        self.purchase_model = self.env['purchase.order']
        self.purchase_approval_model = self.env['purchase.approval']
        self.user_model = self.env['res.users']
        self.mail_model = self.env['mail.mail']

        # Create users
        self.po_approval_head_user = self._create_po_approval_head_user(
            'po_approval_head', [self.group_purchase_manager], self.company1)
        self.po_approval_user = self._create_po_approval_user(
            'po_approval_user', [self.group_purchase_user], self.company1)

        # Create Product category and Products
        self.product_ctg = self._create_product_category()
        self.test_product = self._create_test_product()

        # Create head of all purchase approval like admin and user
        self.approval_head = self._create_approval_head()
        self.approval_user = self._create_approval_user()

        # Prepare purchase order values
        self.po_vals = {
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.test_product.name,
                    'product_id': self.test_product.id,
                    'product_qty': 10.0,
                    'product_uom': self.test_product.uom_po_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DF),
                })],
        }

    def _create_po_approval_head_user(self, login, groups, company):
        """ Create a purchase approval head."""
        group_ids = [group.id for group in groups]
        user = \
            self.user_model.with_context({'no_reset_password': True}).create({
                'name': 'PO Approval Head',
                'login': login,
                'password': login,
                'email': 'po_approval_head@yourcompany.com',
                'company_id': company.id,
                'company_ids': [(4, company.id)],
                'groups_id': [(6, 0, group_ids)]
            })
        return user

    def _create_po_approval_user(self, login, groups, company):
        """ Create a purchase approval user."""
        group_ids = [group.id for group in groups]
        user = \
            self.user_model.with_context({'no_reset_password': True}).create({
                'name': 'PO Approval User',
                'login': login,
                'password': login,
                'email': 'po_approval_user@yourcompany.com',
                'company_id': company.id,
                'company_ids': [(4, company.id)],
                'groups_id': [(6, 0, group_ids)]
            })
        return user

    def _create_approval_head(self):
        """"Create a Purchase Approval Head"""
        approval_head = self.purchase_approval_model.create(
            {'employee_id': self.employee_fpi.id, 'approval_amount': 1000000,
             'co_approval_amount': 1000000})
        self.employee_fpi.parent_id.user_id = self.po_approval_head_user.id
        approval_head.onchange_employee_id()
        approval_head.user_id = self.po_approval_head_user.id
        return approval_head

    def _create_approval_user(self):
        """"Create a Purchase Approval user"""
        approval_user = self.purchase_approval_model.create(
            {'employee_id': self.employee_mit.id, 'approval_amount': 100,
             'co_approval_amount': 500})
        self.employee_mit.parent_id.user_id = self.po_approval_user.id
        approval_user.onchange_employee_id()
        approval_user.user_id = self.po_approval_user.id
        return approval_user

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
        # Approval user don't have enough amount approval rights
        self.po = self.purchase_model.sudo(self.po_approval_user).create(
            self.po_vals)
        self.assertTrue(self.po, 'Purchase: no purchase order created')
        self.assertEqual(self.po.state, 'purchase rfq')
        # Check that mail should be send to supervisor for review
        po_mail = self.mail_model.search([
            ('res_id', '=', self.po.id),
            ('model', '=', 'purchase.order')
        ])
        self.assertNotEqual(po_mail.ids, 0, 'No mail send.')
        # Purchase approval head will review it
        self.po.sudo(self.po_approval_head_user).button_to_request_approve()
        self.po.sudo(self.po_approval_head_user).button_to_approve()
        self.po.sudo(self.po_approval_head_user).button_co_approve()
        # Check that no mail send when approval head review with their rights
        po_mail = self.mail_model.search([
            ('res_id', '=', self.po.id),
            ('model', '=', 'purchase.order')
        ])
        self.assertNotEqual(po_mail.ids, 1, 'More than one mail send.')
        # Check that now PO will be confirmed.
        self.assertEqual(self.po.state, 'purchase')
        self.assertEqual(self.po.picking_count, 1,
                         'Purchase: one picking should be created"')
        self.picking = self.po.picking_ids[0]
        # Clearup with Admin sudo users
        # Cancel picking and delete it
        self.picking.action_cancel()
        self.picking.sudo(SUPERUSER_ID).unlink()
        # Delete mail
        po_mail.sudo(SUPERUSER_ID).unlink()
        # Cancel purchase order and delete it
        self.po.button_cancel()
        self.po.sudo(SUPERUSER_ID).unlink()
