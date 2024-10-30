# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def new(self, vals, origin=None, ref=None):
        """Allows to propose a line based on the RMA information."""
        res = super().new(vals)
        rma_line_id = self.env.context.get("rma_line_id")
        if rma_line_id:
            rma_line = self.env["rma.order.line"].browse(rma_line_id)
            line = self.env["purchase.order.line"].new(
                {
                    "product_id": rma_line.product_id.id,
                }
            )
            line.onchange_product_id()
            line.update(
                {
                    "product_qty": rma_line.qty_to_purchase,
                    "product_uom": rma_line.uom_id.id,
                }
            )
            res.order_line = line
        return res
