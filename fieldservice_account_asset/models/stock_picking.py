# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        equipments = self.env['fsm.equipment']
        for picking in self:
            for move_line in picking.move_line_ids:
                equipments |= equipments.search([
                    ('product_id', '=', move_line.product_id.id),
                    ('lot_id', '=', move_line.lot_id.id),
                    ('asset_id', '!=', False)])
            if equipments:
                equipments_name = ''
                for equipment in equipments:
                    equipments_name += equipment.display_name + ","
                raise ValidationError(
                    _('You can not validate picking of %s equipments as the '
                      'serial number is linked to a running asset.'
                      % (equipments_name)))
        return super().button_validate()
