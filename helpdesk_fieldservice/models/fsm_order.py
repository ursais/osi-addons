# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket',
                                track_visibility='onchange')
