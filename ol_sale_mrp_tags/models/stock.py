# Import Odoo libs
from odoo import models


class StockMove(models.Model):
    """
    Override stock moves to set sale_line_id for mrp uses.
    """

    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        # Ensure sale_line_id is propagated through stock moves
        res = super(StockMove, self)._prepare_procurement_values()
        if self.sale_line_id:
            # Pass sale_line_id into procurement values
            res["sale_line_id"] = self.sale_line_id.id
        return res


class StockRule(models.Model):
    """
    Override stock rules to set sale_order_id gets set on MO.
    """

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
        """
        Override the _prepare_mo_vals method to set the sale_order_id.
        """
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

        # If sale_line_id exists in values, link the MO to the sale order
        sale_line_id = values.get("sale_line_id")
        if sale_line_id:
            sale_order = self.env["sale.order.line"].browse(sale_line_id).order_id
            # Attach sale_order_id to the manufacturing order
            res.update(
                {
                    "sale_order_id": sale_order.id,
                }
            )
        return res

    def _create_manufacturing_orders(self, procurements):
        """
        Override the _create_manufacturing_orders method to pass sale_order_id
        from the sale_line_id to the manufacturing order, even in complex routes.
        """
        for procurement, rule in procurements:
            sale_line = procurement.values.get("sale_line_id")
            if sale_line:
                procurement.values["mrp_so_line_id"] = sale_line
        return super(StockRule, self)._create_manufacturing_orders(procurements)
