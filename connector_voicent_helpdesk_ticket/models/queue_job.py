# Copyright 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models
import time
from datetime import datetime


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.model
    def create(self, vals):
        found = False
        if vals.get('model_name') == 'helpdesk.ticket' and vals.get('name') == 'helpdesk.ticket.voicent_start_campaign':
            record_ids = vals.get('record_ids')
            job_ids = self.env['queue.job'].\
                search([('model_name', '=', 'helpdesk.ticket'),
                        ('name', '=', 'helpdesk.ticket.voicent_start_campaign'),
                        ('date_created', '>', time.strftime('%Y-%m-%d 00:00:00'))])
            for job_id in job_ids:
                if record_ids == job_id.record_ids:
                    found = True
        if found:
            eta = vals.get('eta')
            eta = eta + datetime.timedelta(days=1)
            vals.update({'eta': eta})
        return super().create(vals)
