# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FSMStage(models.Model):
    _inherit = 'fsm.stage'

    equipment_stage_id = fields.Many2one('fsm.stage',
                                         string='Force Equipments Stage')
    asset_action = fields.Selection([('creation', 'Creation'),
                                     ('recovery', 'Recovery')],
                                    string='Asset Action')

    @api.constrains('asset_action', 'company_id')
    def _check_asset_action(self):
        if self.asset_action == 'recovery':
            fsm_stage_count = self.search_count([
                ('asset_action', '=', self.asset_action),
                ('company_id', '=', self.company_id.id)])
            if fsm_stage_count > 1:
                raise ValidationError(_('There can only be one record with'
                                        ' "Recovery" per company.'))
