from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "company_id",
        "partner_id",
        "tax_totals",
        "currency_id",
    )
    def _compute_partner_credit_warning(self):
        for move in self:
            move.partner_credit_warning = ""
