# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FSMEquipment(models.Model):
    _inherit = 'fsm.equipment'

    asset_id = fields.Many2one('account.asset.asset', string='Asset')

    @api.onchange('current_location_id')
    def _on_change_current_location_id(self):
        if self.asset_id:
            raise ValidationError(
                _('Location cannot be changed because this equipment is linked'
                  ' to a running asset.'))

    @api.multi
    def asset_recover(self):
        move = self.env['account.move']
        for equipment in self:
            equipment.asset_id.validate()
            account_move = equipment.asset_id.set_to_close()
            move.browse(account_move.get('res_id')).action_post()

    @api.multi
    def asset_create(self):
        move = self.env['account.move']
        asset = self.env['account.asset.asset']
        for equipment in self:
            move_line_list = []
            product_cost = 0.0
            if equipment.product_id.categ_id.property_cost_method in \
                    ['standard', 'average']:
                product_cost = equipment.product_id.standard_price
            else:
                stock_move_line = self.env['stock.move.line'].search([
                    ('product_id', '=', equipment.product_id.id),
                    ('lot_id', '=', equipment.lot_id.id)])
                product_cost = stock_move_line.move_id.price_unit
            move_line_list.append((0, 0, {
                'account_id': equipment.product_id.categ_id.
                    property_stock_valuation_account_id.id,
                'credit': 0.0,
                'debit': product_cost}))
            move_line_list.append((0, 0, {
                'account_id': equipment.product_id.
                    asset_category_id.account_asset_id.id,
                'credit': product_cost,
                'debit': 0.0}))
            move_vals = {
                'ref': equipment.name,
                'journal_id':
                    equipment.product_id.asset_category_id.journal_id.id,
                'date': datetime.now(),
                'line_ids': move_line_list}
            move.create(move_vals)
            res = asset.create({
                'name': equipment.name,
                'category_id': equipment.product_id.asset_category_id.id,
                'date': datetime.now(),
                'date_first_depreciation': 'manual',
                'first_depreciation_manual_date': datetime.now(),
                'currency_id':
                    equipment.env.user.company_id.currency_id.id,
                'company_id': equipment.env.user.company_id.id,
                'value': product_cost}).id
            return res

    @api.multi
    def change_equipment_stage(self):
        for equipment in self:
            if equipment.stage_id.asset_action == 'creation' and \
                    equipment.current_stock_location_id.usage == 'internal' \
                    and equipment.product_id.asset_category_id:
                equipment.asset_id = self.asset_create()
            elif equipment.stage_id.asset_action == 'recovery':
                if not equipment.serviceprofile_id and equipment.asset_id:
                    self.asset_recover()
                else:
                    raise ValidationError(_("This equipment is still linked to"
                                            " a service profile."))

    def next_stage(self):
        res = super().next_stage()
        self.change_equipment_stage()
        return res

    def previous_stage(self):
        res = super().previous_stage()
        self.change_equipment_stage()
        return res
