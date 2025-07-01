# Import Odoo Libs
from odoo import fields, models
from odoo.addons.repair.models.stock_move import StockMove


# Override _clean_repair_sale_order_line in repair module to reduce database writes
# Improves sale order confirm speed
def _clean_repair_sale_order_line(self):
    lines = self.filtered(lambda m: m.repair_id and m.sale_line_id).mapped(
        "sale_line_id"
    )
    if lines:
        lines.write({"product_uom_qty": 0.0})


# Apply the override
StockMove._clean_repair_sale_order_line = _clean_repair_sale_order_line


class StockMove(models.Model):
    _inherit = "stock.move"

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # END #########
