# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentOrder(models.Model):

    _inherit = "account.payment.order"

    bank_statement_id = fields.Many2one(
        "account.bank.statement",
        compute="_compute_bank_statement_id",
        string="Bank Statement Reference",
    )

    def _compute_bank_statement_id(self):
        for rec in self:
            rec.bank_statement_id = None
            if rec.move_ids:
                temp = [s_id.statement_id.id for s_id in rec.move_ids and rec.move_ids[0].line_ids]
                if temp:
                    rec.bank_statement_id = temp[0]
