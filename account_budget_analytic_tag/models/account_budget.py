# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    analytic_tag_id = fields.Many2one("account.analytic.tag", string="Analytic Tag")

    def _compute_practical_amount(self):
        """Overwrite this method for to count practical_amount based on
        analytic_tag_id on move line."""
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id:
                analytic_line_obj = self.env["account.analytic.line"]
                domain = [
                    ("account_id", "=", line.analytic_account_id.id),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                ]
                if acc_ids:
                    domain += [("general_account_id", "in", acc_ids)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, "read")
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = (
                    "SELECT SUM(amount) from " + from_clause + " where " + where_clause
                )

            else:
                aml_obj = self.env["account.move.line"]
                domain = [
                    ("analytic_tag_ids", "in", line.analytic_tag_id.id),
                    ("account_id", "in", line.general_budget_id.account_ids.ids),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("move_id.state", "=", "posted"),
                ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, "read")
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = (
                    "SELECT sum(credit)-sum(debit) from "
                    + from_clause
                    + " where "
                    + where_clause
                )

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    @api.constrains("general_budget_id", "analytic_account_id", "analytic_tag_id")
    def _must_have_analytical_or_budgetary_or_both(self):
        for record in self:
            if (
                not record.analytic_account_id
                and not record.general_budget_id
                and not record.analytic_tag_id
            ):
                raise ValidationError(
                    _(
                        "You have to enter at least a budgetary position or analytic account"
                        " or analytic tag on a budget line."
                    )
                )
