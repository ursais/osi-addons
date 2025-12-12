# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.constrains("product_uom_qty", "raw_material_production_id", "production_id")
    def _check_negative_quantity_mrp(self):
        """
        Validate that stock moves related to Manufacturing Orders
        have non-negative quantities.
        
        This constraint only applies to moves that are linked to
        Manufacturing Orders (raw materials, finished products, or byproducts).
        """
        for move in self:
            # Only validate moves that are related to Manufacturing Orders
            if not (move.raw_material_production_id or move.production_id):
                continue

            # Skip validation for moves in certain states where negative
            # quantities might be legitimate (e.g., cancelled moves)
            if move.state == "cancel":
                continue

            if move.product_uom_qty < 0:
                mo_name = (
                    move.raw_material_production_id.name
                    if move.raw_material_production_id
                    else move.production_id.name
                )
                raise ValidationError(
                    _(
                        "Stock move %(move_name)s for Manufacturing Order "
                        "%(mo_name)s cannot have a negative quantity (%(qty)s). "
                        "Product: %(product)s"
                    )
                    % {
                        "move_name": move.name or str(move.id),
                        "mo_name": mo_name,
                        "qty": move.product_uom_qty,
                        "product": move.product_id.display_name,
                    }
                )

    def write(self, vals):
        """
        Override write to validate quantities when updating moves.
        """
        result = super().write(vals)
        # Only validate if quantity is being changed
        if "product_uom_qty" in vals:
            self._check_negative_quantity_mrp()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to validate quantities when creating moves.
        """
        moves = super().create(vals_list)
        # Only validate if quantity was set during creation
        if any("product_uom_qty" in vals for vals in vals_list):
            moves._check_negative_quantity_mrp()
        return moves
