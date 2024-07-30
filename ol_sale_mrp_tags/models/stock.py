# Import Odoo libs
from odoo import models


class StockMove(models.Model):
    """
    Override method to set mrp_so_line_id for mrp uses.
    """

    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        # Add sale order line to values
        res["mrp_so_line_id"] = self.sale_line_id
        return res


class StockRule(models.Model):
    """
    Override method to set mrp_sale_id for mrp uses.
    """

    _inherit = "stock.rule"

    # METHODS #########

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        res = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )
        # if mrp_so_line_id is in values, then add the sale order to values
        if values.get("mrp_so_line_id"):
            res.update(
                {
                    "mrp_sale_id": values.get("mrp_so_line_id").order_id.id,
                }
            )
        return res

    # END #########
