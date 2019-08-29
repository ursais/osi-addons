# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for order in self:
            if vals.get('stage_id') and order.stage_id.equipment_stage_id:
                for equipment in order.equipment_ids:
                    equipment.stage_id = \
                        order.stage_id.equipment_stage_id.id
        return res
