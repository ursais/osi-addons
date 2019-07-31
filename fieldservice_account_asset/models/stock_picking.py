# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        fsm_equipments = self.env['fsm.equipment']
        for picking_rec in self:
            for move_line in picking_rec.move_line_ids:
                fsm_equipments |= fsm_equipments.search([
                    ('product_id', '=', move_line.product_id.id),
                    ('lot_id', '=', move_line.lot_id.id),
                    ('asset_id', '!=', False)])
            if fsm_equipments:
                equipments_name = ''
                for rec in fsm_equipments:
                    equipments_name += rec.display_name + ","
                raise ValidationError(
                    _('You can not validate picking of %s equipments as the '
                      'serial number is linked to a running asset.'
                      % (equipments_name)))
        return super(StockPicking, self).button_validate()
