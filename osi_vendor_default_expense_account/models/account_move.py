# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_account_id(self):
        res = super(AccountMoveLine, self)._compute_account_id()
        for move_line in self:
            if (
                move_line.move_id.partner_id
                and move_line.move_id.partner_id.use_default_expense_account
                and move_line.move_id.partner_id.default_expense_account_id
                and move_line.move_id.move_type == "in_invoice"
            ):
                move_line.account_id = move_line.partner_id.default_expense_account_id
        return res

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)
        partner = (
            self.move_id.partner_id
            and self.move_id.partner_id.commercial_partner_id
            or values.get("partner_id")
            and self.env["res.partner"]
            .browse(values["partner_id"])
            .commercial_partner_id
        )
        if (
            partner
            and partner.use_default_expense_account
            and partner.default_expense_account_id
            and (
                self.move_id.move_type == "in_invoice"
                or self._context.get("default_type") == "in_invoice"
            )
        ):
            values["account_id"] = partner.default_expense_account_id.id
        return values
