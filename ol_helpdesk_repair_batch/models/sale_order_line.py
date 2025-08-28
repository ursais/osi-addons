# Import Odoo libs
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # COLUMNS ###

    is_repair_component = fields.Boolean(
        string="Repair Component",
        help="Technical field to mark lines that come from repair added parts.",
    )

    # END #######
    # METHODS ###

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        # Skip stock rules for repair component lines (like in core repair)
        lines_without_repair_parts = self.filtered(lambda l: not l.is_repair_component)
        return super(
            SaleOrderLine, lines_without_repair_parts
        )._action_launch_stock_rule(previous_product_uom_qty)

    # END #######
