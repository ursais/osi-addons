# Copyright (C) 2020 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    helpdesk_ticket_id = fields.\
        Many2one('helpdesk.ticket', string="Helpdesk Ticket")

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if not vals.get('carrier_id', False):
            vals['carrier_id'] = self.helpdesk_ticket_id.carrier_id.id
        return vals
