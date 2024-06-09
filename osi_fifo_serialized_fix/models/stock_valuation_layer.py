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
        new_vals_list = []
        for val in vals_list:
            stock_move_id = self.env["stock.move"].browse(val.get("stock_move_id"))
            svl_id = self.env["stock.valuation.layer"].browse(val.get("stock_valuation_layer_id"))
            if stock_move_id:
                if len(stock_move_id.move_line_ids) > 1:
                    lotless_move_lines = stock_move_id.move_line_ids.filtered(lambda x: x.lot_id.id == False)
                    for lot_id in stock_move_id.move_line_ids.mapped("lot_id"):
                        move_lines = stock_move_id.move_line_ids.filtered(lambda x: x.lot_id == lot_id)
                        sign = 1 if val["quantity"] >= 0 else -1
                        quantity = sum(move_lines.mapped("quantity"))
                        new_val = val.copy()
                        new_val["quantity"] = quantity * sign
                        new_val["remaining_qty"] = quantity if sign > 0 else 0
                        new_val["value"] = quantity * new_val.get("unit_cost", 0.0) * sign
                        new_val["remaining_value"] = new_val["value"] if sign > 0 else 0
                        new_val["lot_ids"] = [lot_id.id]
                        new_vals_list.append(new_val)
                    for product in lotless_move_lines.mapped("product_id"):
                        move_lines = stock_move_id.move_line_ids.filtered(lambda x: x.product_id == product)
                        sign = 1 if val["quantity"] >= 0 else -1
                        quantity = sum(move_lines.mapped("quantity"))
                        new_val = val.copy()
                        new_val["quantity"] = quantity * sign
                        new_val["remaining_qty"] = quantity if sign > 0 else 0
                        new_val["value"] = quantity * new_val.get("unit_cost", 0.0) * sign
                        new_val["remaining_value"] = new_val["value"] if sign > 0 else 0
                        new_vals_list.append(new_val)
                else:
                    if stock_move_id.move_line_ids.lot_id:
                        val["lot_ids"] = [stock_move_id.move_line_ids.lot_id.id]
                    new_vals_list.append(val)
            elif svl_id:
                new_val = val.copy()
                new_val["lot_ids"] = [svl_id.lot_ids.ids]
                new_vals_list.append(new_val)
            else:
                new_vals_list = vals_list
        res = super().create(new_vals_list)
        for layer in res.filtered(
            lambda l: l.stock_move_id.lot_ids or l.stock_valuation_layer_id.lot_ids
        ):
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

            # Product is consumed in Manufacturing Order
            if layer.stock_move_id.raw_material_production_id:
                total_lot_price = 0
                for lot in layer.lot_ids:
                    move_lines = layer.stock_move_id.move_line_ids.filtered(lambda x: x.lot_id.id == lot.id)
                    move_quantity = sum(move_line.quantity for move_line in move_lines)
                    real_price = move_lines.mapped("lot_id").mapped("real_price")[0]
                    lot.write({"real_price": real_price})
                layer.remaining_value = 0
                layer.value = -(real_price * move_quantity)

                layer.unit_cost = real_price

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
