# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    helpdesk_service_request_line = fields.One2many(
        'helpdesk.service.request.line',
        'ticket_id',
        string='Service Requests',
    )

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            ticket_stage = self.env['helpdesk.stage'].browse(
                vals.get('stage_id'))
            if ticket_stage.is_close:
                for ticket in self:
                    if ticket.helpdesk_service_request_line:
                        open_lines =\
                            ticket.helpdesk_service_request_line.filtered(
                                lambda x: x.fsm_stage_id.is_close)
                        if (open_lines and len(open_lines.ids) != len(
                                ticket.helpdesk_service_request_line.ids)):
                            raise ValidationError(
                                _('Please complete all service request related'
                                  ' with this ticket.'))
        return super(HelpdeskTicket, self).write(vals)


class HelpdeskServiceRequestLine(models.Model):
    _name = 'helpdesk.service.request.line'
    _description = 'Helpdesk Service Request Line'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
    )
    fsm_order_id = fields.Many2one(
        'fsm.order',
        string='Service Request',
    )
    fsm_stage_id = fields.Many2one(
        'fsm.stage',
        string='Stage',
        related='fsm_order_id.stage_id'
    )
    fsm_order = fields.Integer(
        string='SR ID',
        related='fsm_order_id.id'
    )
    fsm_order_name = fields.Char(
        string='SR Name',
        related='fsm_order_id.name'
    )
    fsm_customer_id = fields.Many2one(
        'res.partner',
        string='FSM Customer',
        related='fsm_order_id.customer_id'
    )
    fsm_location_id = fields.Many2one(
        'fsm.location',
        string='FSM Location'
    )
