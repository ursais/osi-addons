# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_geoengine import geo_model
except ImportError:
    _logger.info('base_geoengine module not found.')


class FSMOrder(geo_model.GeoModel):
    _inherit = 'fsm.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket',
                                track_visibility='onchange')
