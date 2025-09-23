# Import Odoo libs
from odoo import api, models


class AccountMove(models.Model):
    """
    Inherit account move to remove the oob
    credit limit warning as we are using our own.
    """

    _inherit = "account.move"

    # METHODS #####

    @api.depends(
        "company_id",
        "partner_id",
        "tax_totals",
        "currency_id",
    )
    def _compute_partner_credit_warning(self):
        # Remove out of box partner credit warning
        for move in self:
            move.partner_credit_warning = ""

    # END #########
