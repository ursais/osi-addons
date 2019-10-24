# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    inventory_location_id = fields.Many2one(
        related='fsm_location_id.inventory_location_id', store=True)

    @api.onchange('fsm_location_id')
    def onchange_location_id(self):
        res = super()._onchange_fsm_location_id_partner()
        if self.fsm_location_id:
            self.warehouse_id = self.fsm_location_id.default_warehouse_id
        return res
