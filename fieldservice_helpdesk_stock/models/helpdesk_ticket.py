# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def action_inventory_request(self):
        res = super(HelpdeskTicket, self).action_inventory_request()
        for fsmo in self.fsm_order_ids:
            fsmo.action_inventory_request()
        return res

    def action_inventory_confirm(self):
        res = super(HelpdeskTicket, self).action_inventory_confirm()
        for fsmo in self.fsm_order_ids:
            fsmo.action_inventory_confirm()
        return res

    def action_inventory_cancel(self):
        res = super(HelpdeskTicket, self).action_inventory_cancel()
        for fsmo in self.fsm_order_ids:
            fsmo.action_inventory_cancel()
        return res

    def action_inventory_reset(self):
        res = super(HelpdeskTicket, self).action_inventory_reset()
        for fsmo in self.fsm_order_ids:
            fsmo.action_inventory_reset()
        return res
