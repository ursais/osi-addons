# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        for move in res:
            if move.fsm_order_line_id:
                move.update({
                    'helpdesk_ticket_line_id':
                        move.fsm_order_line_id.helpdesk_ticket_line_id.id})
            elif (move.helpdesk_ticket_line_id and
                  move.helpdesk_ticket_line_id.fsm_order_line_id):
                move.update({
                    'fsm_order_line_id':
                        move.helpdesk_ticket_line_id.fsm_order_line_id.id})
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def create(self, vals):
        res = super(ProcurementGroup, self).create(vals)
        for procurement in res:
            ticket = procurement.helpdesk_ticket_id
            if ticket:
                ticket_line = ticket.line_ids.filtered(
                    lambda x: x.fsm_order_line_id)
                if ticket_line:
                    fsm_order_id = ticket_line[0].fsm_order_line_id.order_id
                    procurement.write({'fsm_order_id': fsm_order_id.id})
        return res
