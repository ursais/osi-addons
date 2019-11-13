# Copyright (C) 2019 Pavlov Media
# License Proprietary. Do not copy, share nor distribute.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
            if record.ticket_id.stage_id.is_close is False:
                record.ticket_id.write({'resolution': record.resolution,
                                        'stage_id': record.stage_id.id})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    def action_complete(self):
        if not self.date_end:
            raise ValidationError(_("Cannot move to Complete " +
                                    "until 'Actual End' is filled in"))
        if not self.resolution:
            raise ValidationError(_("Cannot move to Complete " +
                                    "until 'Resolution' is filled in"))
        if self.ticket_id:
            if self.ticket_id.stage_id.is_close is True:
                return self.write({'stage_id': self.env.ref(
                    'fieldservice.fsm_stage_completed').id})
            else:
                self.write({'stage_id': self.env.ref(
                    'fieldservice.fsm_stage_completed').id})
                view_id = self.env.ref(
                    'helpdesk_fieldservice.fsm_order_close_wizard_view_form').id
                return {
                    'view_id': view_id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'fsm.order.close.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_ticket_id': self.ticket_id.id,
                                'default_team_id': self.ticket_id.team_id.id,
                                'default_resolution': self.resolution}
                }
        else:
            return self.write({'stage_id': self.env.ref(
                'fieldservice.fsm_stage_completed').id})
