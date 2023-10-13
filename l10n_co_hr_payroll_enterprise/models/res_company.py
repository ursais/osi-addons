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


class ResCompany(models.Model):
    _inherit = 'res.company'

    smmlv_value = fields.Monetary("SMMLV", currency_field='currency_id', readonly=False)
    uvt_value = fields.Monetary("UVT", currency_field='currency_id', readonly=False)
    stm_value = fields.Monetary("Monthly transportation allowance", currency_field='currency_id', readonly=False)

    # times
    daily_overtime = fields.Float("% Daily overtime", readonly=False, default=25.0)
    overtime_night_hours = fields.Float("% Overtime night hours", readonly=False, default=75.0)
    hours_night_surcharge = fields.Float("% Hours night surcharge", readonly=False, default=35.0)
    sunday_holiday_daily_overtime = fields.Float("% Sunday and Holiday daily overtime", readonly=False,
                                                 default=100.0)
    daily_surcharge_hours_sundays_holidays = fields.Float("% Daily surcharge hours on sundays and holidays",
                                                          readonly=False, default=75.0)
    sunday_night_overtime_holidays = fields.Float("% Sunday night overtime and holidays", readonly=False,
                                                  default=150.0)
    sunday_holidays_night_surcharge_hours = fields.Float("% Sunday and holidays night surcharge hours",
                                                         readonly=False, default=110.0)

    # Test
    edi_payroll_is_not_test = fields.Boolean(string="Production environment", default=False, readonly=False)

    # Enable/disable electronic payroll for company
    edi_payroll_enable = fields.Boolean(string="Enable electronic payroll for this company", default=False,
                                        readonly=False)

    # Test
    edi_payroll_test_set_id = fields.Char(string="TestSetId")

    # Software ID and pin
    edi_payroll_id = fields.Char(string="Software ID", readonly=False)
    edi_payroll_pin = fields.Char(string="Software PIN", readonly=False)

    # Consolidated payroll
    edi_payroll_consolidated_enable = fields.Boolean(string="Enable consolidated electronic payroll for this company",
                                                     default=False, readonly=False)
