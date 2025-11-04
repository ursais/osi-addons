# Import Odoo libs
from odoo import models


class StockMove(models.Model):
    """
    Override stock moves to set sale_line_id for mrp uses.
    """

    _inherit = "stock.move"

    # Methods #####

    def _prepare_procurement_values(self):
        # Ensure sale_line_id is propagated through stock moves
        res = super()._prepare_procurement_values()
        if self.sale_line_id:
            # Pass sale_line_id into procurement values
            res["sale_line_id"] = self.sale_line_id.id
        return res

    # END #########
