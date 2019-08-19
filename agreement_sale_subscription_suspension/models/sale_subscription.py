# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleSubscriptionSuspension(models.Model):
    _inherit = 'sale.subscription'

    def suspend_service_profile(self):
        for subscription_id in self:
            sp_ids = self.env['agreement.serviceprofile'].search([
                ('agreement_id', '=', subscription_id.agreement_id.id)])
            if sp_ids:
                sp_ids.write({'state': 'suspended'})

    def activate_service_profile(self):
        for subscription_id in self:
            sp_ids = self.env['agreement.serviceprofile'].search([
                ('agreement_id', '=', subscription_id.agreement_id.id)])
            if sp_ids:
                sp_ids.write({'state': 'active'})

    def action_suspend(self):
        self.suspend_service_profile()
        return super().action_suspend()

    def action_re_activate(self):
        self.activate_service_profile()
        return super().action_re_activate()

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            stage_id = self.env['sale.subscription.stage'].search(
                [('id', '=', vals['stage_id'])])
            if stage_id.name == 'Suspended':
                self.suspend_service_profile()
            elif stage_id.name == "In Progress":
                self.activate_service_profile()
        return res
