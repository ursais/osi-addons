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
                record.ticket_id.write({'resolution': record.resolution})
                record.ticket_id.write({'stage_id': record.stage_id.id})
                # Run the action that is on the ticket stage
                ctx = dict({})
                ctx.update({
                    'active_id': record.ticket_id.id,
                    'active_model': 'helpdesk.ticket'
                })
                record.stage_id.action_id.with_context(ctx).run()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
