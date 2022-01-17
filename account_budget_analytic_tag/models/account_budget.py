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
                self.env.cr.execute(
                    """
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id=%s
                        AND (date between %s
                        AND %s)
                        AND general_account_id=ANY(%s)""",
                    (line.analytic_account_id.id, date_from, date_to, acc_ids),
                )
                result = self.env.cr.fetchone()[0] or 0.0

            else:
                self.env.cr.execute(
                    """
                    SELECT SUM(credit) - SUM(debit)
                    FROM account_move_line aml
                    LEFT JOIN account_move am ON aml.move_id = am.id
                    LEFT JOIN
                        account_account_tag_account_move_line_rel aat
                        ON aat.account_move_line_id = aml.id
                    WHERE state=%s
                    AND account_id in %s
                        AND (aml.date between %s
                        AND %s)
                        AND aat.account_account_tag_id=%s""",
                    (
                        "posted",
                        tuple(line.general_budget_id.account_ids.ids),
                        date_from,
                        date_to,
                        line.analytic_tag_id.id or 0.0,
                    ),
                )
                result = self.env.cr.fetchone()[0]
            line.practical_amount = result

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
