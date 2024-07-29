# Import Odoo libs
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        res["mrp_so_line_id"] = self.sale_line_id
        return res


class StockRule(models.Model):
    _inherit = "stock.rule"

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
        if values.get("mrp_so_line_id"):
            res.update(
                {"mrp_sale_id": values.get("mrp_so_line_id").order_id.id,}
            )
        return res
