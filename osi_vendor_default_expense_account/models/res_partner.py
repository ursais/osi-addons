# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    default_expense_account_id = fields.Many2one(
        "account.account", string="Default Expense Account"
    )
    use_default_expense_account = fields.Boolean()
