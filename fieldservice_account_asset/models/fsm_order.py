# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    @api.multi
    def write(self, vals):
        rec = super(FSMOrder, self).write(vals)
        for order in self:
            if vals.get('stage_id') and order.stage_id.equipment_stage_id:
                for equipment_rec in order.equipment_ids:
                    equipment_rec.stage_id = \
                        order.stage_id.equipment_stage_id.id
        return rec
