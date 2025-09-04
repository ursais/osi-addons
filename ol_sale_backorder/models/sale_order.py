# Import Odoo libs
from odoo import models


class SaleOrderLine(models.Model):
    """Inherit SO to check backorder qty functionality before confirm."""

    _inherit = "sale.order"

    # METHODS #####

    def action_confirm(self):
        """
        Before confirmation, check that there are no product lines that
        prevent selling the product due to not allowing backorders.
        """
        for line in self.order_line:
            line._check_no_backorders_caps()
        return super().action_confirm()

    # END #####
