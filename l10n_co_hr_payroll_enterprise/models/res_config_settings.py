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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_co_hr_payroll = fields.Boolean(string='Colombian Payroll')

    smmlv_value = fields.Monetary(related="company_id.smmlv_value", string="SMMLV", readonly=False,
                                  currency_field='currency_id')
    uvt_value = fields.Monetary(related="company_id.uvt_value", string="UVT", readonly=False,
                                currency_field='currency_id')
    stm_value = fields.Monetary(related="company_id.stm_value",
                                string="Monthly transportation allowance", readonly=False,
                                currency_field='currency_id')

    # times
    daily_overtime = fields.Float(
        related="company_id.daily_overtime",
        string="% Daily",
        readonly=False
    )
    overtime_night_hours = fields.Float(
        related="company_id.overtime_night_hours",
        string="% Night hours",
        readonly=False
    )
    hours_night_surcharge = fields.Float(
        related="company_id.hours_night_surcharge",
        string="% Night hours",
        readonly=False
    )
    sunday_holiday_daily_overtime = fields.Float(
        related="company_id.sunday_holiday_daily_overtime",
        string="% Sunday and Holiday daily",
        readonly=False
    )
    daily_surcharge_hours_sundays_holidays = fields.Float(
        related="company_id.daily_surcharge_hours_sundays_holidays",
        string="% Daily hours on sundays and holidays",
        readonly=False
    )
    sunday_night_overtime_holidays = fields.Float(
        related="company_id.sunday_night_overtime_holidays",
        string="% Sunday night and holidays",
        readonly=False
    )
    sunday_holidays_night_surcharge_hours = fields.Float(
        related="company_id.sunday_holidays_night_surcharge_hours",
        string="% Sunday and holidays night hours",
        readonly=False
    )

    # Test
    edi_payroll_is_not_test = fields.Boolean(related="company_id.edi_payroll_is_not_test",
                                             string="Production environment", default=False, readonly=False)

    # Enable/disable electronic payroll for company
    edi_payroll_enable = fields.Boolean(related="company_id.edi_payroll_enable",
                                        string="Enable electronic payroll for this company", default=False,
                                        readonly=False)

    # Test
    edi_payroll_test_set_id = fields.Char(related="company_id.edi_payroll_test_set_id", string="TestSetId",
                                          readonly=False)

    # Software ID and pin
    edi_payroll_id = fields.Char(related="company_id.edi_payroll_id", string="Software ID", readonly=False)
    edi_payroll_pin = fields.Char(related="company_id.edi_payroll_pin", string="Software PIN", readonly=False)

    # Consolidated payroll
    edi_payroll_consolidated_enable = fields.Boolean(related="company_id.edi_payroll_consolidated_enable",
                                                     string="Enable consolidated electronic payroll for this company",
                                                     default=False, readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['edi_payroll_is_not_test'] = self.env.company.edi_payroll_is_not_test
        res['edi_payroll_enable'] = self.env.company.edi_payroll_enable
        res['edi_payroll_consolidated_enable'] = self.env.company.edi_payroll_consolidated_enable
        return res
