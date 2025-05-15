# Import Odoo Libs
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # METHODS ######

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res['note'] = self.note
        return res

    # END ##########
