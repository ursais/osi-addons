# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base_geoengine import geo_model


class FSMOrder(geo_model.GeoModel):
    _inherit = 'fsm.order'

    def action_inventory_confirm(self):
        res = super(FSMOrder, self).action_inventory_confirm()
        for order in self:
            order.procurement_group_id.helpdesk_ticket_id = order.ticket_id.id
        return res

    def write(self, vals):
        res = super(FSMOrder, self).write(vals)
        if 'ticket_id' in vals:
            for line in self.line_ids:
                if line.state in ('draft', 'requested', 'cancelled'):
                    if line.helpdesk_ticket_line_id:
                        line.helpdesk_ticket_line_id.ticket_id = \
                            vals['ticket_id']
                    else:
                        line.helpdesk_ticket_line_id = \
                            self.env['helpdesk.ticket.line'].create({
                                'product_id': line.product_id.id,
                                'name': line.name,
                                'qty_requested': line.qty_requested,
                                'qty_ordered': line.qty_ordered,
                                'product_uom_id': line.product_uom_id.id,
                                'ticket_id': vals['ticket_id'],
                                'fsm_order_line_id': line.id,
                                'state': line.state,
                            })
        return res
