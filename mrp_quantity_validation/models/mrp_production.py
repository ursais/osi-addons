# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.constrains("move_raw_ids", "move_finished_ids", "move_byproduct_ids")
    def _check_negative_quantities(self):
        """
        Validate that all moves related to this Manufacturing Order
        have non-negative quantities.
        
        This constraint ensures that:
        - Raw material moves have non-negative quantities
        - Finished product moves have non-negative quantities
        - Byproduct moves have non-negative quantities
        """
        for production in self:
            # Check raw material moves
            negative_raw_moves = production.move_raw_ids.filtered(
                lambda m: m.product_uom_qty < 0
            )
            if negative_raw_moves:
                raise ValidationError(
                    _(
                        "Manufacturing Order %(mo_name)s has negative quantities "
                        "on raw material moves:\n%(moves)s"
                    )
                    % {
                        "mo_name": production.name,
                        "moves": "\n".join(
                            [
                                f"  - {move.product_id.display_name}: "
                                f"{move.product_uom_qty}"
                                for move in negative_raw_moves
                            ]
                        ),
                    }
                )

            # Check finished product moves
            negative_finished_moves = production.move_finished_ids.filtered(
                lambda m: m.product_uom_qty < 0
            )
            if negative_finished_moves:
                raise ValidationError(
                    _(
                        "Manufacturing Order %(mo_name)s has negative quantities "
                        "on finished product moves:\n%(moves)s"
                    )
                    % {
                        "mo_name": production.name,
                        "moves": "\n".join(
                            [
                                f"  - {move.product_id.display_name}: "
                                f"{move.product_uom_qty}"
                                for move in negative_finished_moves
                            ]
                        ),
                    }
                )

            # Check byproduct moves
            negative_byproduct_moves = production.move_byproduct_ids.filtered(
                lambda m: m.product_uom_qty < 0
            )
            if negative_byproduct_moves:
                raise ValidationError(
                    _(
                        "Manufacturing Order %(mo_name)s has negative quantities "
                        "on byproduct moves:\n%(moves)s"
                    )
                    % {
                        "mo_name": production.name,
                        "moves": "\n".join(
                            [
                                f"  - {move.product_id.display_name}: "
                                f"{move.product_uom_qty}"
                                for move in negative_byproduct_moves
                            ]
                        ),
                    }
                )

    def write(self, vals):
        """
        Override write to validate quantities when moves are modified.
        """
        result = super().write(vals)
        # Trigger validation if move fields are being modified
        if any(
            field in vals
            for field in ["move_raw_ids", "move_finished_ids", "move_byproduct_ids"]
        ):
            self._check_negative_quantities()
        return result

    def action_confirm(self):
        """
        Override to validate quantities before confirming the MO.
        """
        self._check_negative_quantities()
        return super().action_confirm()
