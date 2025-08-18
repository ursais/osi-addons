# Import Odoo libs
from odoo import api, models


class AccountMove(models.Model):
    """Inherit Account Move for method changes."""

    _inherit = "account.move"
    # METHODS ######

    @api.depends("amount_residual", "move_type", "state", "company_id")
    def _compute_payment_state(self):
        super()._compute_payment_state()

        for move in self:
            if move.payment_state == "paid" and move.line_ids.mapped("sale_line_ids"):
                sale_lines = move.line_ids.mapped("sale_line_ids")
                if sale_lines:
                    sale_lines._compute_invoice_status()

    # END ##########
