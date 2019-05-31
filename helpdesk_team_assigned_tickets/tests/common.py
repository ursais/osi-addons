# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class HelpdeskTransactionCase(TransactionCase):

    def setUp(self):
        super(HelpdeskTransactionCase, self).setUp()
        
        #Set up company, manager, and user
        self.main_company_id = self.env.ref('base.main_company').id
        self.helpdesk_manager = self.env['res.users'].create({
            'company_id': self.main_company_id,
            'name': 'Helpdesk Manager',
            'login': 'hm',
            'email': 'hm@example.com',
            'groups_id': [(6, 0, [self.env.ref('helpdesk.group_helpdesk_manager').id])]
        })
        self.helpdesk_user = self.env['res.users'].create({
            'company_id': self.main_company_id,
            'name': 'Helpdesk User',
            'login': 'hu',
            'email': 'hu@example.com',
            'groups_id': [(6, 0, [self.env.ref('helpdesk.group_helpdesk_user').id])]
        })
