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


from odoo import fields, models


class HrRuleInput(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    input_type_id = fields.Many2one('hr.payslip.input.type', string='Payslip Input Type', required=True)

    name = fields.Char(related='input_type_id.name', readonly=True)
    code = fields.Char(related='input_type_id.code', readonly=True)
    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=True)
