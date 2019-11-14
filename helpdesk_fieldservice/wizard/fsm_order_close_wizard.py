# Copyright (C) 2019 Pavlov Media
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMOrderCloseWizard(models.TransientModel):
    _name = "fsm.order.close.wizard"
    _description = "FSM Close - Option to Close Ticket"

    resolution = fields.Text(string="Resolution")
    team_id = fields.Many2one('helpdesk.team', string="Helpdesk Team")
    stage_id = fields.Many2one('helpdesk.stage', string="Stage")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

    @api.multi
    def action_close_ticket(self):
        for record in self:
            if not record.ticket_id.stage_id.is_close:
                record.ticket_id.write({'resolution': record.resolution,
                                        'stage_id': record.stage_id.id})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
