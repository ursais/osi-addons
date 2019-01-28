# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    fsm_order_ids = fields.One2many('fsm.order', 'ticket_id',
                                    string='Service Orders')
    fsm_location_id = fields.Many2one('fsm.location', string='FSM Location')

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            ticket_stage = self.env['helpdesk.stage'].browse(
                vals.get('stage_id'))
            if ticket_stage.is_close:
                for ticket in self:
                    if ticket.fsm_order_ids:
                        open_orders =\
                            ticket.fsm_order_ids.filtered(
                                lambda x: x.stage_id.is_close)
                        if (open_orders and len(open_orders.ids) != len(
                                ticket.fsm_order_ids)):
                            raise ValidationError(
                                _('Please complete all service orders '
                                  'related to this ticket to close it.'))
        return super(HelpdeskTicket, self).write(vals)
