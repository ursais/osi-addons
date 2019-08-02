# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
                _('Location is not change because equipment is linked to '
                  'a running asset.'))

    @api.multi
    def do_recover(self):
        for equip_rec in self:
            if equip_rec.stage_id.asset_action == 'recovery':
                equip_rec.change_equipment_stage()

    @api.multi
    def change_equipment_stage(self):
        account_move_obj = self.env['account.move']
        account_asset_obj = self.env['account.asset.asset']
        for equip_rec in self:
            if equip_rec.stage_id.asset_action == 'creation' and \
                    equip_rec.current_stock_location_id.\
                    usage == 'internal' and equip_rec.product_id.\
                    asset_category_id:
                move_line_list = []
                product_cost = 0.0
                if equip_rec.product_id.categ_id. \
                        property_cost_method in ['standard', 'average']:
                    product_cost = equip_rec.product_id.standard_price
                elif equip_rec.product_id.categ_id. \
                        property_cost_method == 'fifo':
                    stock_move_line = self.env['stock.move.line'].search([
                        ('product_id', '=', equip_rec.product_id.id),
                        ('lot_id', '=', equip_rec.lot_id.id)])
                    product_cost = stock_move_line.move_id.price_unit
                move_line_list.append(
                    (0, 0, {'account_id': equip_rec.product_id.categ_id.
                            property_stock_valuation_account_id.id,
                            'credit': 0.0,
                            'debit': product_cost
                            }))
                move_line_list.append(
                    (0, 0, {'account_id': equip_rec.product_id.
                            asset_category_id.account_asset_id.id,
                            'credit': product_cost,
                            'debit': 0.0
                            }))
                move_vals = {
                    'ref': equip_rec.name,
                    'journal_id':
                    equip_rec.product_id.asset_category_id.journal_id.id,
                    'date': datetime.now(),
                    'line_ids': move_line_list
                }
                account_move_obj.create(move_vals)
                equip_rec.asset_id = account_asset_obj.create(
                    {'name': equip_rec.name,
                     'category_id': equip_rec.product_id.asset_category_id.id,
                     'date': datetime.now(),
                     'date_first_depreciation': 'manual',
                     'first_depreciation_manual_date': datetime.now(),
                     'currency_id':
                     equip_rec.env.user.company_id.currency_id.id,
                     'company_id': equip_rec.env.user.company_id.id,
                     'value': product_cost}).id
            elif equip_rec.stage_id.asset_action == 'recovery':
                if not equip_rec.serviceprofile_id and equip_rec.asset_id:
                    equip_rec.asset_id.validate()
                    account_move = equip_rec.asset_id.set_to_close()
                    account_move_obj.browse(
                        account_move.get('res_id')).action_post()
                else:
                    raise ValidationError(
                        _("This equipment is still linked to a service"
                            " profile."))

    def next_stage(self):
        rec = super(FSMEquipment, self).next_stage()
        self.change_equipment_stage()
        return rec

    def previous_stage(self):
        rec = super(FSMEquipment, self).previous_stage()
        self.change_equipment_stage()
        return rec
