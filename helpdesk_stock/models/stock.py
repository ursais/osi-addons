# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    helpdesk_ticket_line_id = fields.Many2one('helpdesk.ticket.line',
                                              'Helpdesk Ticket Line')

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        for line in res.mapped('helpdesk_ticket_line_id').sudo():
            line.qty_delivered = line._get_delivered_qty()
        return res

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            for move in self:
                if move.state == 'done':
                    for line in res.mapped('helpdesk_ticket_line_id').sudo():
                        line.qty_delivered = line._get_delivered_qty()
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', 'Helpdesk Ticket')


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        res = super(ProcurementRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom,
            location_id, name, origin, values, group_id)
        if values.get('helpdesk_ticket_line_id', False):
            res['helpdesk_ticket_line_id'] = values['helpdesk_ticket_line_id']
        return res


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
                    [('inventory_stage', '=', 'requested'),
                     ('warehouse_id', '=', ptype.warehouse_id.id)])
                ptype.count_hdesk_requests = len(res)

    def get_action_helpdesk_requests(self):
        return self._get_action('helpdesk_stock.action_stock_helpdesk_ticket')
