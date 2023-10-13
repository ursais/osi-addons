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
from odoo.addons import decimal_precision as dp


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    edi_rate = fields.Float(string='Edi Rate (%)', digits=dp.get_precision('Payroll Rate'),
                            default=100.0, compute="compute_edi_rate", store=True, required=True)

    edi_quantity = fields.Integer(string='Edi Quantity', default=0, compute="compute_edi_quantity", required=True,
                                  store=True)

    def compute_edi_rate(self):
        for rec in self:
            if rec.salary_rule_id.edi_percent_select == 'default':
                return rec.rate
            else:
                return rec.salary_rule_id.compute_edi_percent(rec.slip_id)

    def compute_edi_quantity(self):
        for rec in self:
            if rec.salary_rule_id.type_concept == 'earn' and rec.salary_rule_id.edi_quantity_select == 'auto':
                worked_days_line = rec.env['hr.payslip.worked_days'].search([
                    ('payslip_id', '=', rec.slip_id.id),
                    ('code', '=', rec.code)
                ])
                if rec.salary_rule_id.earn_category in (
                        'vacation_common',
                        'vacation_compensated',
                        'licensings_maternity_or_paternity_leaves',
                        'licensings_permit_or_paid_licenses',
                        'licensings_suspension_or_unpaid_leaves',
                        'incapacities_common',
                        'incapacities_professional',
                        'incapacities_working',
                        'legal_strikes',
                        'primas'
                ):
                    return worked_days_line[0]['number_of_days'] if worked_days_line else 0
                elif rec.salary_rule_id.earn_category in (
                        'daily_overtime',
                        'overtime_night_hours',
                        'hours_night_surcharge',
                        'sunday_holiday_daily_overtime',
                        'daily_surcharge_hours_sundays_holidays',
                        'sunday_night_overtime_holidays',
                        'sunday_holidays_night_surcharge_hours'
                ):
                    return worked_days_line[0]['number_of_hours'] if worked_days_line else 0
                else:
                    return rec.quantity
            else:
                return rec.quantity
