from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _prepare_move_line_vals(self):
        self.ensure_one()

        return {
            "name": self.ref,
            "move_id": False,
            "partner_id": self.partner_id.id,
            "currency_id": self.journal_id.company_id.currency_id.id,
            "account_id": self.account_id.id,
            "debit": self.debit,
            "credit": self.credit,
            "amount_currency": self.amount_currency,
        }
