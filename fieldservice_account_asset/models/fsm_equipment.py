# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FSMEquipment(models.Model):
    _inherit = 'fsm.equipment'

    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    asset_location_id = fields.Many2one(
        'stock.location', string='Location',
        help='Inventory location when the equipment turned into an asset')

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
            action = equipment.asset_id.set_to_close()
            move.browse(action.get('res_id')).action_post()
            move_line = self.env['account.move.line'].search([
                ('move_id', '=', move.id),
                ('account_id', '=', equipment.asset_id.category_id.
                 account_depreciation_expense_id.id)])
            equipment.asset_id = False
            product_cost = move_line.debit
            # Move the inventory item back to where it was
            stock_move = self.env['stock.move'].create({
                'name': 'Asset Recovery - ' + equipment.name,
                'reference': 'Asset Recovery - ' + equipment.name,
                'product_id': equipment.product_id.id,
                'product_uom_qty': 1.0,
                'product_uom': equipment.product_id.uom_id.id,
                'price_unit': product_cost,
                'date': datetime.now(),
                'location_id': equipment.current_stock_location_id.id,
                'location_dest_id': equipment.asset_location_id.id,
            })
            self.env['stock.move.line'].create({
                'reference': 'Asset Recovery - ' + equipment.name,
                'product_id': equipment.product_id.id,
                'product_uom_id': equipment.product_id.uom_id.id,
                'lot_id': equipment.lot_id.id,
                'qty_done': 1.0,
                'date': datetime.now(),
                'location_id': equipment.current_stock_location_id.id,
                'location_dest_id': equipment.asset_location_id.id,
                'move_id': stock_move.id,
            })
            stock_move._action_confirm()
            stock_move._action_done()
            equipment.asset_location_id = False

    @api.multi
    def asset_create(self):
        asset = self.env['account.asset.asset']
        for equipment in self:
            product_cost = 0.0
            if equipment.product_id.categ_id.property_cost_method in \
                    ['standard', 'average']:
                product_cost = equipment.product_id.standard_price
            else:
                stock_move_line = self.env['stock.move.line'].search([
                    ('product_id', '=', equipment.product_id.id),
                    ('lot_id', '=', equipment.lot_id.id)])
                product_cost = stock_move_line.move_id.price_unit
            # Move the inventory item to the Fixed Asset inventory location
            stock_move = self.env['stock.move'].create({
                'name': 'Asset Creation - ' + equipment.name,
                'reference': 'Asset Creation - ' + equipment.name,
                'product_id': equipment.product_id.id,
                'product_uom_qty': 1.0,
                'product_uom': equipment.product_id.uom_id.id,
                'price_unit': product_cost,
                'date': datetime.now(),
                'location_id': equipment.current_stock_location_id.id,
                'location_dest_id': equipment.company_id.asset_location_id.id,
            })
            self.env['stock.move.line'].create({
                'reference': 'Asset Creation - ' + equipment.name,
                'product_id': equipment.product_id.id,
                'product_uom_id': equipment.product_id.uom_id.id,
                'lot_id': equipment.lot_id.id,
                'qty_done': 1.0,
                'date': datetime.now(),
                'location_id': equipment.current_stock_location_id.id,
                'location_dest_id': equipment.company_id.asset_location_id.id,
                'move_id': stock_move.id,
            })
            # Keep the current location to move it back there when the asset
            # is recovered
            equipment.asset_location_id = \
                equipment.current_stock_location_id.id
            stock_move._action_confirm()
            stock_move._action_done()
            # Create the asset
            asset = asset.create({
                'name': equipment.name,
                'code': equipment.name,
                'category_id': equipment.product_id.asset_category_id.id,
                'date': datetime.now(),
                'date_first_depreciation': 'manual',
                'first_depreciation_manual_date': datetime.now(),
                'currency_id': equipment.env.user.company_id.currency_id.id,
                'company_id': equipment.env.user.company_id.id,
                'value': product_cost})
            asset.onchange_category_id()
            if asset.category_id.open_asset:
                asset.validate()
            return asset.id

    @api.multi
    def change_equipment_stage(self):
        for equipment in self:
            if equipment.stage_id.asset_action == 'creation' and \
                    equipment.current_stock_location_id.usage == 'internal' \
                    and equipment.product_id.asset_category_id and \
                    not equipment.asset_id:
                equipment.asset_id = equipment.asset_create()
            elif equipment.stage_id.asset_action == 'recovery':
                if not equipment.serviceprofile_ids and equipment.asset_id:
                    equipment.asset_recover()
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
