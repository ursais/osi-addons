# Import Odoo Libs
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """
    Update purchase order lines with fields
    """

    _inherit = "purchase.order.line"

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # END #########
    # METHODS ######

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
        res["note"] = self.note
        return res

    @api.depends("product_qty", "product_uom", "company_id")
    def _compute_price_unit_and_date_planned_and_name(self):
        """
        Compute the `price_unit`, `date_planned`, and `name` fields for purchase order lines.

        This override skips computation for lines that are:
        - Already in 'purchase' state (confirmed), **and**
        - Already have a `price_unit` set

        This avoids overwriting confirmed data during recomputation, which can happen
        if dependent fields like `product_qty` or `product_uom` are changed.
        """
        # Exclude lines that are already confirmed and have price_unit set
        self = self - self.filtered(
            lambda l: l.id and l.order_id.state == "purchase" and l.price_unit
        )
        # Call the original compute method for the remaining records
        return super(
            PurchaseOrderLine, self
        )._compute_price_unit_and_date_planned_and_name()

    def _update_move_date_deadline(self, new_date):
        """
        Override core sync to support skip_move_sync context.
        """
        if self.env.context.get("skip_move_sync"):
            # Skip syncing deadlines to moves → prevents recursion with stock.move.write
            return
        return super()._update_move_date_deadline(new_date)

    # END ##########
