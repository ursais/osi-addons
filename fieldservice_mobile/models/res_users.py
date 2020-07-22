# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    create_fsm_worker = fields.Boolean('FSM Worker')
    fsm_worker_id = fields.Many2one('fsm.person', 'Related FSM Worker')

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        fsm_wizard_obj = self.env['fsm.wizard']
        if vals.get('sel_groups_1_9_10') == 9 and res.create_fsm_worker:
            fsm_wizard_obj.action_convert_person(res.partner_id)
            worker = self.env['fsm.person'].search([('partner_id', '=', res.partner_id.id)])
            res.fsm_worker_id = worker.id
        return res

    @api.multi
    def write(self, vals):
        fsm_wizard_obj = self.env['fsm.wizard']
        if vals.get('create_fsm_worker'):
            fsm_wizard_obj.action_convert_person(self.partner_id)
            worker = self.env['fsm.person'].search([('partner_id', '=', self.partner_id.id)])
            vals.update({'fsm_worker_id': worker.id})
        return super(ResUsers, self).write(vals)
