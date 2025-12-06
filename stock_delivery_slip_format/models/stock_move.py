# Copyright (C) 2024, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    """Extend stock.move to add helper methods for delivery slip formatting."""

    _inherit = "stock.move"

    def _get_formatted_ordered_qty(self):
        """
        Get ordered quantity formatted as integer (no decimals).

        :return: integer quantity as string
        """
        if not self.product_uom_qty:
            return "0"
        try:
            return str(int(self.product_uom_qty))
        except (ValueError, TypeError):
            return "0"

    def _get_formatted_delivered_qty(self):
        """
        Get delivered quantity formatted as integer (no decimals).
        Sums qty_done from all move lines.

        :return: integer quantity as string
        """
        if not self.move_line_ids:
            return "0"
        try:
            # Filter out None values and sum qty_done
            qty_done = sum(
                line.qty_done for line in self.move_line_ids if line.qty_done
            )
            return str(int(qty_done)) if qty_done else "0"
        except (ValueError, TypeError):
            return "0"
