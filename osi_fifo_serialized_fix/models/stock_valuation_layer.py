# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    real_price = fields.Float()


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many("stock.production.lot", string="Lot ID's", readonly=True)
    
    repair_type = fields.Selection([
        ("add", "Add"),
        ("remove", "Remove")
    ])

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for layer in res.filtered(lambda l:l.stock_move_id.lot_ids):
            layer.lot_ids = [(6, 0, layer.stock_move_id.lot_ids.ids)]

            #Update the lot price when we do incoming lots
            if layer.stock_move_id.location_id.usage == 'supplier':
                layer.lot_ids.write({'real_price':layer.value})

            #Update the lot price for the raw material moves.
            #Update the layer values for raw materual moves
            if layer.stock_move_id.raw_material_production_id:
                total_lot_price = 0
                for lot in layer.lot_ids:
                    all_lot_layers = self.search([('lot_ids', 'in', lot.id), ('id', '!=', layer.id)]).filtered(lambda l : l.lot_ids and len(l.lot_ids.ids)==1)
                    total_qty = sum([svl.quantity for svl in all_lot_layers])
                    total_value = sum([svl.value for svl in all_lot_layers])
                    svl_value = total_value / total_qty if total_qty else 1.0
                    lot.write({'real_price':svl_value})
                    total_lot_price+=svl_value
                layer.value=-total_lot_price
                layer.unit_cost = -(total_lot_price / layer.quantity if layer.quantity else 1)

            #Update the lot price for the FG moves.
            #Update the layer values for FG moves
            if layer.stock_move_id.production_id:
                production = layer.stock_move_id.production_id
                work_center_cost = 0
                consumed_moves = production.move_raw_ids.filtered(lambda x: x.state == 'done')
                finished_move = layer.stock_move_id
                if finished_move:
                    finished_move.ensure_one()
                    for work_order in production.workorder_ids:
                        time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                        duration = sum(time_lines.mapped('duration'))
                        time_lines.write({'cost_already_recorded': True})
                        work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
                    qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
                    extra_cost = production.extra_cost * qty_done
                    raw_sn_price = sum(lot.real_price for lot in consumed_moves.mapped('lot_ids'))
                    final_sn_price = (raw_sn_price + work_center_cost + extra_cost) / qty_done
                    production.lot_producing_id.real_price = final_sn_price
                    layer.value = final_sn_price
                    layer.unit_cost= final_sn_price

        return res

    def svl_lots_update(self):
        # Update lot_ids on svl for existing records.
        for svl in self:
            svl.lot_ids = [
                (6, 0, svl.stock_move_id.mapped("move_line_ids").mapped("lot_id").ids)
            ]
