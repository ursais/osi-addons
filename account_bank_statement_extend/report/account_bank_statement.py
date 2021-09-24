# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def get_base_reconcile_entries(self):
        for lines in self:
            move_line_ids = self.env['account.move.line'].search([("statement_id","=", lines.id)])
        return move_line_ids
