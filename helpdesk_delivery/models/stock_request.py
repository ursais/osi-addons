# Copyright (C) 2020 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method")

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        if res.get('carrier_id', False):
            res.update({
                'carrier_id': self.helpdesk_ticket_id.carrier_id.id or False,
            })
        return res
