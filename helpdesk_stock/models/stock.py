# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockRequest(models.Model):
    _inherit = "stock.request"

    ticket_id = fields.Many2one(
        'helpdesk.ticket', string="Helpdesk Ticket",
        ondelete='cascade', index=True, copy=False)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super(StockMoveLine, self)._action_done()
        for rec in self:
            for rec in rec.move_id.allocation_ids:
                request = rec.stock_request_id
                if request.state == 'done' and request.ticket_id:
                    request.ticket_id.request_stage = 'done'
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', 'Helpdesk Ticket')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    helpdesk_ticket_id = fields.Many2one(
        related="group_id.helpdesk_ticket_id", string="Helpdesk Ticket",
        store=True)


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    helpdesk_selectable = fields.Boolean(string="Helpdesk Ticket Lines")


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    count_hdesk_requests = fields.Integer(compute='_compute_hdesk_request')

    def _compute_hdesk_request(self):
        for ptype in self:
            if ptype.code == 'outgoing':
                res = self.env['helpdesk.ticket'].search(
                    [('request_stage', '=', 'draft'),
                     ('warehouse_id', '=', ptype.warehouse_id.id)])
                ptype.count_hdesk_requests = len(res)

    def get_action_helpdesk_requests(self):
        return self._get_action('helpdesk_stock.'
                                'action_stock_helpdesk_ticket_request')
