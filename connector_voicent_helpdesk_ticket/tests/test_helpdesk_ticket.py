# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestHelpdeskTicket(TransactionCase):

    def setUp(self):
        super(TestHelpdeskTicket, self).setUp()
        self.backend_voicent_model = self.env['backend.voicent']
        self.res_partner_model = self.env['res.partner']
        self.helpdesk_ticket_model = self.env['helpdesk.ticket']
        self.helpdesk_stage_model = self.env['helpdesk.stage']

    def test_helpdesk_ticket_change_stage(self):
        self.res_partner_id = self.res_partner_model.create(
            {'name': 'Test Azure Interior',
             'company_type': 'person',
             'can_call': True})

        self.helpdesk_stage_model_id = self.helpdesk_stage_model.create(
            {'name': 'New'})

        self.helpdesk_stage_in_progress_id = self.helpdesk_stage_model.create(
            {'name': 'In Progress'})

        self.helpdesk_ticket_id = self.helpdesk_ticket_model.create(
            {'name': 'Test Kitchen collapsing',
             'partner_id': self.res_partner_id.id,
             'stage_id': self.helpdesk_stage_model_id.id})

        self.backend_voicent_id = self.backend_voicent_model.create(
            {'name': 'Test',
             'host': 'localhost',
             'port': '8155',
             'callerid': '0000000000',
             'line': '4',
             'active': True,
             'call_line_ids': [(0, 0, {'name': 'call 1',
                                       'applies_on': False,
                                       'helpdesk_ticket_stage_id':
                                       self.helpdesk_stage_in_progress_id.id,
                                       'msgtype': 'tts',
                                       'msginfo': 'Hello World'
                                       })],
             'time_line_ids': [(0, 0, {'name': 'Call Time 1',
                                       'time': 10.0}),
                               (0, 0, {'name': 'Call Time 2',
                                       'time': 11.0}),
                               (0, 0, {'name': 'Call Time 3',
                                       'time': 12.0}),
                               (0, 0, {'name': 'Call Time 4',
                                       'time': 16.46})]
             })
        self.backend_voicent_id._run_update_next_call()

        self.helpdesk_ticket_id.write(
            {'stage_id': self.helpdesk_stage_in_progress_id.id})
