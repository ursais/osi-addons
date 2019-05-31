# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    assigned_tickets = fields.Integer(string='Active Tickets',
        compute='_compute_assigned_tickets')

    @api.multi
    def _compute_assigned_tickets(self):
        ticket_data = self.env['helpdesk.ticket'].\
            read_group([('user_id', '!=', False),
                        ('team_id', 'in', self.ids),
                        ('stage_id.is_close', '!=', True)],['team_id'], ['team_id'])
        mapped_data = dict((data['team_id'][0], data['team_id_count'])
            for data in ticket_data)
        for team in self:
            team.assigned_tickets = mapped_data.get(team.id, 0)