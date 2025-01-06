# Import Odoo libs
from odoo import api, fields, models


class AccountMove(models.Model):
    """Add compute field to Account Move."""

    _inherit = "account.move"

    # COLUMNS ######

    po_price_difference = fields.Boolean(
        "PO Line Difference",
        compute="_compute_po_line_price_difference",
        store=True,
    )

    # END ##########

    # METHODS ######

    @api.depends("line_ids.po_line_price_difference")
    def _compute_po_line_price_difference(self):
        for move in self:
            po_price_difference = False
            if move.move_type == "in_invoice":  # Only for Vendor Bills
                po_price_difference = any(
                    line.po_line_price_difference for line in move.line_ids
                )
            move.po_price_difference = po_price_difference

    # END ##########
