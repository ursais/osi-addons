# Copyright (C) 2019 - TODAY, Open Source Integrators
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
                        open_orders = \
                            ticket.fsm_order_ids.filtered(
                                lambda x: x.stage_id.is_closed)
                        if (open_orders and len(open_orders.ids) != len(
                                ticket.fsm_order_ids)):
                            raise ValidationError(
                                _('Please complete all service orders '
                                  'related to this ticket to close it.'))
        return super(HelpdeskTicket, self).write(vals)

    def _location_contact_fill(self, loc):
        """loc is a boolean that lets us know if this is coming from the
        partner onchange or the location onchange"""
        if loc:
            if self.fsm_location_id and self.partner_id:
                if self.partner_id.service_location_id != self.fsm_location_id:
                    self.partner_id = False
        else:
            if self.partner_id:
                if not self.fsm_location_id:
                    self.fsm_location_id = self.partner_id.service_location_id

    @api.onchange('fsm_location_id')
    def _onchange_fsm_location_id_partner(self):
        if self.fsm_location_id:
            self._location_contact_fill(True)
            if self.fsm_location_id and not self.partner_id:
                return {'domain': {
                    'partner_id':
                        [('service_location_id', '=',
                          self.fsm_location_id.name)]}}
        else:
            return {'domain': {'partner_id': [('id', '!=', None)]}}

    @api.onchange('partner_id')
    def _onchange_partner_id_location(self):
        if self.partner_id:
            self._location_contact_fill(False)
