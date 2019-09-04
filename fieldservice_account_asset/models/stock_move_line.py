# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, _
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        equipments = self.env['fsm.equipment']
        for line in self:
            equipments |= equipments.search([
                ('product_id', '=', line.product_id.id),
                ('lot_id', '=', line.lot_id.id),
                ('asset_id', '!=', False)])
            if equipments:
                equipments_name = ''
                for equipment in equipments:
                    equipments_name += equipment.display_name + ","
                raise ValidationError(
                    _('You cannot validate this transfer as it includes'
                      ' equipments linked to running assets: %s.'
                      % (equipments_name)))
        return super()._action_done()
