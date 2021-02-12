# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder)
        for move in res:
            if (
                move.product_id.tracking in ["serial", "lot"]
                and move.picking_id.picking_type_id.code == "outgoing"
            ):
                svl_ids = []
                test_vals = self.env["stock.valuation.layer"].search(
                    [("product_id", "=", move.product_id.id)]
                )
                for line_id in move.move_line_ids:
                    for valuation in test_vals:
                        if line_id.lot_id in valuation.lot_ids and valuation.value > 0:
                            if not self.check_found_vals(valuation.id, svl_ids):
                                svl_ids.append((valuation.id, 1, [line_id.lot_id.id]))
                                break
                            else:
                                self.increment_qty(
                                    valuation.id, svl_ids, line_id.lot_id.id
                                )
                if len(svl_ids) > 1:
                    final_layers = []
                    for layer in move.stock_valuation_layer_ids:
                        layer.sudo().unlink()
                    for svl_id in svl_ids:
                        val = move.product_id._prepare_out_svl_vals(
                            svl_id[1], self.env.user.company_id
                        )
                        val_obj = self.env["stock.valuation.layer"].browse(svl_id[0])
                        val["unit_cost"] = val_obj.unit_cost
                        val["value"] = val_obj.unit_cost * svl_id[1] * -1
                        val["company_id"] = self.env.user.company_id.id
                        val["lot_ids"] = [(6, 0, svl_id[2])]
                        if line_id.product_id.tracking == 'lot':
                            val["quantity"] = line_id.qty_done * -1
                        final_layers.append(val)
                    final_layers = self.env["stock.valuation.layer"].create(final_layers)
                    move.write(
                        {"stock_valuation_layer_ids": [(6, 0, final_layers.ids)]}
                    )
                else:
                    if len(move.stock_valuation_layer_ids.ids) > 1:
                        svl = self.env["stock.valuation.layer"].browse(svl_ids[0][0])
                        val = move.stock_valuation_layer_ids[0]
                        val.unit_cost = -1 * svl.unit_cost
                        for layer in move.stock_valuation_layer_ids:
                            layer.sudo().unlink()
                        move.write({"stock_valuation_layer_ids": [6, 0, val.id]})
                    else:
                        svl = self.env["stock.valuation.layer"].browse(svl_ids[0][0])
                        move.stock_valuation_layer_ids.unit_cost = -1 * svl.unit_cost
                        move.stock_valuation_layer_ids.value = -1 \
                            * move.stock_valuation_layer_ids.quantity \
                            * move.stock_valuation_layer_ids.unit_cost
        return res

    def increment_qty(self, id, svl_ids, lot_id):
        index = 0
        for svl_id in svl_ids:
            if svl_id[0] == id:
                if lot_id not in svl_id[2]:
                    svl_id[2].append(lot_id)
                svl_ids[index] = (svl_id[0], svl_id[1] + 1, svl_id[2])
            index += 1

    def check_found_vals(self, id, svl_ids):
        for svl_id in svl_ids:
            if id == svl_id[0]:
                return True
        return False

    def _create_in_svl(self, forced_quantity=None):
        res = super()._create_in_svl(forced_quantity)
        for move in self:
            for layer in res:
                if layer.stock_move_id.id == move.id:
                    layer.lot_ids = [(6, 0, move.lot_ids.ids)]
        return res
