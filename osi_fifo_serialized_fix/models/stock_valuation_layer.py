# Copyright (C) 2023, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.tools import float_is_zero, float_round


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    real_price = fields.Float()


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many("stock.lot", string="Lot ID's", readonly=True)
    repair_type = fields.Selection([('add', 'ADD'), ('remove', 'Remove')], string="Repair Type")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for layer in res.filtered(lambda l:l.stock_move_id.lot_ids or l.stock_valuation_layer_id.lot_ids):
            layer.lot_ids = [(6, 0, layer.stock_move_id.lot_ids.ids)]

            #Below code is only for Cabintouch as they are using pre-component / pick component location as a Production location
            if layer.stock_move_id.mapped('move_dest_ids').mapped('raw_material_production_id'):
                total_lot_price = 0
                for lot in layer.lot_ids:
                    all_lot_layers = self.search([('lot_ids', 'in', lot.id), ('id', '!=', layer.id)])
                    total_qty = sum([svl.quantity for svl in all_lot_layers])
                    total_value = sum([svl.value for svl in all_lot_layers])
                    svl_value = total_value / total_qty if total_qty else 1.0
                    lot.write({'real_price':svl_value})
                    total_lot_price+=svl_value
                layer.value=-total_lot_price
                layer.unit_cost = -(total_lot_price / layer.quantity if layer.quantity else 1)
                layer.remaining_value = layer.value
                layer.lot_ids = [(6, 0, [])]
            #===================================================================================
            #Update the lot price when we do incoming lots
            #update the lot_ids for linked layer.
            #i.g. Landed cost layers, Price diff layers.
            if layer.stock_valuation_layer_id and not layer.lot_ids:
                layer.lot_ids = layer.stock_valuation_layer_id.lot_ids
            if layer.stock_move_id.location_id.usage in ('inventory', 'supplier'):
                layer_ids = self.search([('lot_ids','in',layer.lot_ids.ids)])
                total_qty = sum(layer_ids.mapped("quantity"))
                total_value = sum(layer_ids.mapped("value"))
                layer.lot_ids.write({'real_price': total_value/total_qty if total_qty else 1})

            #Update the lot price for the raw material moves.
            #Update the layer values for raw materual moves
            if layer.stock_move_id.raw_material_production_id:
                total_lot_price = 0
                for lot in layer.lot_ids:
                    all_lot_layers = self.search([('lot_ids', 'in', lot.id), ('id', '!=', layer.id)])
                    # all_moves = all_lot_layers.mapped('stock_move_id') or self.env['stock.move']
                    # rawmaterial_moves = all_lot_layers.mapped('stock_move_id').mapped('move_dest_ids').filtered(lambda l : l.raw_material_production_id) or self.env['stock.move']
                    # required_moves = all_moves - rawmaterial_moves

                    # required_layers = self.search([('stock_move_id','in',required_moves.ids)])
                    total_qty = sum([svl.quantity for svl in all_lot_layers])
                    total_value = sum([svl.value for svl in all_lot_layers])
                    svl_value = total_value / total_qty if total_qty else 1.0
                    lot.write({'real_price':svl_value})
                    total_lot_price+=svl_value
                layer.value=-total_lot_price
                layer.unit_cost = -(total_lot_price / layer.quantity if layer.quantity else 1)
                layer.remaining_value = layer.value

            if layer.stock_move_id.production_id and layer.stock_move_id.product_id.cost_method in ('fifo', 'average'):
                layer.stock_move_id.production_id.lot_producing_id.real_price = layer.stock_move_id.price_unit

            #Update the lot price for the FG moves.
            #Update the layer values for FG moves
#             if layer.stock_move_id.production_id:
#                 production = layer.stock_move_id.production_id
#                 work_center_cost = 0
#                 consumed_moves = production.move_raw_ids.filtered(lambda x: x.state == 'done')
#                 finished_move = layer.stock_move_id
#                 if finished_move and consumed_moves.mapped('lot_ids'):
#                     finished_move.ensure_one()
# #                    total_cost = finished_move.price_unit - (sum(-m.stock_valuation_layer_ids.value for m in consumed_moves.filtered(lambda sm : sm.product_id.tracking == 'serial')))
#                     qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
#                     raw_sn_price = sum(lot.real_price for lot in consumed_moves.mapped('lot_ids'))
#                     raw_non_sn_price = - sum(consumed_moves.filtered(lambda l:l.product_id.tracking !='serial').sudo().stock_valuation_layer_ids.mapped('value'))
#                     total_cost = finished_move.price_unit + raw_non_sn_price
#                     byproduct_moves = production.move_byproduct_ids.filtered(lambda m: m.state in ('done', 'cancel') and m.quantity_done > 0)
#                     byproduct_cost_share = 0
#                     for byproduct in byproduct_moves:
#                         if byproduct.cost_share == 0:
#                             continue
#                         byproduct_cost_share += byproduct.cost_share
#                         if byproduct.product_id.cost_method in ('fifo', 'average') and byproduct.product_id.tracking =='serial':
#                             byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)
#                             byproduct.stock_valuation_layer_ids.write({'unit_cost':byproduct.price_unit, 
#                                                                        'value':byproduct.price_unit* byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id),
#                                                                        'remaining_value' : byproduct.price_unit* byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)
#                                                                        })
#                             byproduct.lot_ids.write({'real_price':byproduct.price_unit})
#                         else:
#                             byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)
#                             byproduct.stock_valuation_layer_ids.write({'unit_cost':byproduct.price_unit, 
#                                                                        'value':byproduct.price_unit* byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id),
#                                                                        'remaining_value':byproduct.price_unit* byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)})
#                     if finished_move.product_id.cost_method in ('fifo', 'average'):
#                         finished_move.price_unit = total_cost * float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001) / qty_done
#                         production.lot_producing_id.real_price = finished_move.price_unit
#                         layer.value = finished_move.price_unit
#                         layer.unit_cost= finished_move.price_unit
        return res

    def svl_lots_update(self):
        # Update lot_ids on svl for existing records.
        for svl in self:
            svl.lot_ids = [
                (6, 0, svl.stock_move_id.mapped("move_line_ids").mapped("lot_id").ids)
            ]






