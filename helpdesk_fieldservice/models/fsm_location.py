# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields
from odoo.addons.base_geoengine import geo_model


class FSMLocation(geo_model.GeoModel):
    _inherit = 'fsm.location'

    ticket_count = fields.Integer(
        compute='_compute_ticket_count',
        string='# Tickets'
    )

    @api.multi
    def _compute_ticket_count(self):
        for location in self:
            res = self.env['helpdesk.ticket'].search_count(
                [('fsm_location_id', '=', location.id)])
            location.ticket_count = res or 0

    @api.multi
    def action_view_ticket(self):
        for location in self:
            ticket_ids = self.env['helpdesk.ticket'].search(
                [('fsm_location_id', '=', location.id)])
            action = self.env.ref(
                'helpdesk_fieldservice.action_fsm_location_ticket').read()[0]
            action['context'] = {}
            if len(ticket_ids) > 1:
                action['domain'] = [('id', 'in', ticket_ids.ids)]
            elif len(ticket_ids) == 1:
                action['views'] = [(
                    self.env.ref('helpdesk.helpdesk_ticket_view_form').id,
                    'form')]
                action['res_id'] = ticket_ids.ids[0]
            return action
