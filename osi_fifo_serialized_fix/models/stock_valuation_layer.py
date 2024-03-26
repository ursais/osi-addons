# Copyright (C) 2023, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    real_price = fields.Float()


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    lot_ids = fields.Many2many("stock.lot", string="Lot ID's")
    repair_type = fields.Selection([("add", "ADD"), ("remove", "Remove")])

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for layer in res.filtered(
            lambda l: l.stock_move_id.lot_ids or l.stock_valuation_layer_id.lot_ids
        ):
            layer.lot_ids = [(6, 0, layer.stock_move_id.lot_ids.ids)]

            # Update the lot price when we do incoming lots
            # update the lot_ids for linked layer.
            # i.g. Landed cost layers, Price diff layers.
            if layer.stock_valuation_layer_id and not layer.lot_ids:
                layer.lot_ids = layer.stock_valuation_layer_id.lot_ids

            # Update lot price for Purchase and Inventory Adjustment Increase
            if layer.stock_move_id.location_id.usage in ("inventory", "supplier"):
                layer_ids = self.search([("lot_ids", "in", layer.lot_ids.ids)])
                total_qty = sum(layer_ids.mapped("quantity"))
                total_value = sum(layer_ids.mapped("value"))
                layer.lot_ids.write(
                    {"real_price": total_value / total_qty if total_qty else 1}
                )

            # Update the lot price for the raw material moves.
            # Update the layer values for raw materual moves
            if layer.stock_move_id.raw_material_production_id:
                total_lot_price = 0
                for lot in layer.lot_ids:
                    all_lot_layers = self.search(
                        [("lot_ids", "in", lot.id), ("id", "!=", layer.id)]
                    )
                    total_qty = sum([svl.quantity for svl in all_lot_layers])
                    total_value = sum([svl.value for svl in all_lot_layers])
                    svl_value = total_value / total_qty if total_qty else 1.0
                    lot.write({"real_price": svl_value})
                    total_lot_price += svl_value
                layer.value = -total_lot_price

                layer.unit_cost = -(
                    total_lot_price / layer.quantity if layer.quantity else 1
                )
                layer.remaining_value = layer.value
                layer.lot_ids = [(6, 0, [])]

            if (
                layer.stock_move_id.production_id
                and layer.stock_move_id.product_id.cost_method in ("fifo", "average")
            ):
                layer.stock_move_id.production_id.lot_producing_id.real_price = (
                    layer.stock_move_id.price_unit
                )

            # For inventory Decrease
            if (
                layer.stock_move_id
                and layer.stock_move_id.location_dest_id.usage in ("inventory")
                and "inventory_mode" in self._context.keys()
            ):
                layer.unit_cost = sum(layer.mapped("lot_ids").mapped("real_price"))
                layer.value = layer.unit_cost * layer.quantity
        return res

    def svl_lots_update(self):
        # Update lot_ids on svl for existing records.
        for svl in self:
            svl.lot_ids = [
                (6, 0, svl.stock_move_id.mapped("move_line_ids").mapped("lot_id").ids)
            ]
