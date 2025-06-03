# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    """Inherit Sale Order for method changes."""

    _inherit = "sale.order"

    # METHODS ######

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if self.sale_payment_method_id:
            values.update({"sale_payment_method_id": self.sale_payment_method_id.id})
        return values

    # END ##########
