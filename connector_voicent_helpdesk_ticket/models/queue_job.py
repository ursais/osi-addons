# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QueueJob(models.Model):
    """ Job status and result """
    _inherit = 'queue.job'

    helpdesk_ticket_id = fields.Many2one(
        'helpdesk.ticket', 'Ticket',
    )
