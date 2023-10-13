# -*- coding: utf-8 -*-
#
#   Jorels S.A.S. - Copyright (C) 2019-2023
#
#   This file is part of l10n_co_hr_payroll_enterprise.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/>.
#
#   email: info@jorels.com
#


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DeductionLine(models.Model):
    _name = 'l10n_co_hr_payroll.deduction.line'
    _description = 'Deduction details'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(help="The code that can be used in the salary rules", compute="_compute_rule", store=True)
    amount = fields.Float("Amount")

    rule_input_id = fields.Many2one('hr.rule.input', string='Rule input', copy=True, required=True,
                                    domain=[('input_id.type_concept', '=', 'deduction')])
    category = fields.Selection([
        ('health', 'Health'),
        ('pension_fund', 'Pension fund'),
        ('pension_security_fund', 'Pension security fund'),
        ('pension_security_fund_subsistence', 'Pension security fund subsistence'),
        ('voluntary_pension', 'Voluntary pension'),
        ('withholding_source', 'Withholding source'),
        ('afc', 'Afc'),
        ('cooperative', 'Cooperative'),
        ('tax_lien', 'Tax lien'),
        ('complementary_plans', 'Complementary plans'),
        ('education', 'Education'),
        ('refund', 'Refund'),
        ('debt', 'Debt'),
        ('trade_unions', 'Trade unions'),
        ('sanctions_public', 'Sanctions public'),
        ('sanctions_private', 'Sanctions private'),
        ('libranzas', 'Libranzas'),
        ('third_party_payments', 'Third party payments'),
        ('advances', 'Advances'),
        ('other_deductions', 'Other deductions')
    ], string="Category", compute="_compute_rule", store=True)

    @api.depends("rule_input_id")
    def _compute_rule(self):
        for rec in self:
            rec.name = rec.rule_input_id.name
            rec.code = rec.rule_input_id.code
            rec.category = rec.rule_input_id.input_id.deduction_category

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("The deduction amount must always be greater than 0 for: %s") % rec.name)
