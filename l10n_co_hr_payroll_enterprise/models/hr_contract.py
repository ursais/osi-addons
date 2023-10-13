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


from odoo import fields, models, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    type_worker_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_workers", string="Type worker")
    subtype_worker_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.subtype_workers", string="Subtype worker")
    high_risk_pension = fields.Boolean(string="High risk pension", default=False)
    integral_salary = fields.Boolean(string="Integral salary", default=False)
    type_contract_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_contracts", string="Type contract")
    payroll_period_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.payroll_periods", string="Payroll period",
                                        compute="_compute_payroll_period_id", store=True)

    @api.depends('schedule_pay')
    def _compute_payroll_period_id(self):
        for rec in self:
            values = {
                'monthly': 5,
                'quarterly': 6,
                'semi-annually': 6,
                'annually': 6,
                'weekly': 1,
                'bi-weekly': 4,
                'bi-monthly': 6,
            }
            if rec.schedule_pay:
                rec.payroll_period_id = values[rec.schedule_pay]
            else:
                rec.payroll_period_id = None
