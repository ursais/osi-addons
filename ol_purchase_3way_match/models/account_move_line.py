# Import Odoo libs
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """Add compute field to Account Move Line."""

    _inherit = "account.move.line"

    # COLUMNS ######

    po_line_price_difference = fields.Boolean(
        "PO Line Difference",
        compute="_compute_po_line_price_difference",
        store=True,
    )

    # END ##########

    # METHODS ######

    @api.depends("purchase_line_id", "price_unit")
    def _compute_po_line_price_difference(self):
        for line in self:
            po_line_price_difference = False
            if line.purchase_line_id and line.product_id.detailed_type in [
                "product",
                "consu",
            ]:
                po_price = line.purchase_line_id.price_unit
                bill_price = line.price_unit
                po_line_price_difference = bool(po_price != bill_price)
            line.po_line_price_difference = po_line_price_difference

    # END ##########
