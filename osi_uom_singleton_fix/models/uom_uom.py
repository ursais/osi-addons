# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class UoM(models.Model):
    """Inherit UoM model to fix singleton error in _compute_price method."""

    _inherit = "uom.uom"

    def _compute_price(self, price, to_unit):
        """
        Override _compute_price to handle empty recordset case.

        This fixes the ValueError: Expected singleton: uom.uom() error that
        occurs during BOM structure computations when the UoM recordset is
        empty (e.g., when bom.product_tmpl_id.uom_id is missing).

        Args:
            price (float): The price to convert
            to_unit (recordset): The target UoM to convert to

        Returns:
            float: The converted price, or 0.0 if recordset is empty
        """
        # Guard clause: if recordset is empty, return 0.0 to prevent singleton error
        if not self:
            return 0.0

        # Call parent method if recordset is not empty
        return super()._compute_price(price, to_unit)
