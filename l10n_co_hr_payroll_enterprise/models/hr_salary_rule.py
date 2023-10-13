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
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    input_ids = fields.One2many('hr.rule.input', 'input_id', string='Inputs', copy=True)

    type_concept = fields.Selection([
        ('earn', 'Earn'),
        ('deduction', 'Deduction'),
        ('other', 'Other')
    ], string="Type concept", default="other", required=True)

    earn_category = fields.Selection([
        ('basic', 'Basic'),
        ('vacation_common', 'Vacation common'),
        ('vacation_compensated', 'Vacation compensated'),
        ('primas', 'Primas'),
        ('primas_non_salary', 'Primas non salary'),
        ('layoffs', 'Layoffs'),
        ('layoffs_interest', 'Layoffs interest'),
        ('licensings_maternity_or_paternity_leaves', 'Licensings maternity or paternity leaves'),
        ('licensings_permit_or_paid_licenses', 'Licensings permit or paid licenses'),
        ('licensings_suspension_or_unpaid_leaves', 'Licensings suspension or unpaid leaves'),
        ('endowment', 'Endowment'),
        ('sustainment_support', 'Sustainment support'),
        ('telecommuting', 'Telecommuting'),
        ('company_withdrawal_bonus', 'Company withdrawal bonus'),
        ('compensation', 'Compensation'),
        ('refund', 'Refund'),
        ('transports_assistance', 'Transports assistance'),
        ('transports_viatic', 'Transports viatic'),
        ('transports_non_salary_viatic', 'Transports non salary viatic'),
        ('daily_overtime', 'Daily overtime'),
        ('overtime_night_hours', 'Overtime night hours'),
        ('hours_night_surcharge', 'Hours night surcharge'),
        ('sunday_holiday_daily_overtime', 'Sunday and Holiday daily overtime'),
        ('daily_surcharge_hours_sundays_holidays', 'Daily surcharge hours on sundays and holidays'),
        ('sunday_night_overtime_holidays', 'Sunday night overtime and holidays'),
        ('sunday_holidays_night_surcharge_hours', 'Sunday and holidays night surcharge hours'),
        ('incapacities_common', 'Incapacities common'),
        ('incapacities_professional', 'Incapacities professional'),
        ('incapacities_working', 'Incapacities working'),
        ('bonuses', 'Bonuses'),
        ('bonuses_non_salary', 'Non salary bonuses'),
        ('assistances', 'Assistances'),
        ('assistances_non_salary', 'Non salary assistances'),
        ('legal_strikes', 'Legal strikes'),
        ('other_concepts', 'Other concepts'),
        ('other_concepts_non_salary', 'Non salary other concepts'),
        ('compensations_ordinary', 'Compensations ordinary'),
        ('compensations_extraordinary', 'Compensations extraordinary'),
        ('vouchers', 'Vouchers'),
        ('vouchers_non_salary', 'Vouchers non salary'),
        ('vouchers_salary_food', 'Vouchers salary food'),
        ('vouchers_non_salary_food', 'Vouchers non salary food'),
        ('commissions', 'Commissions'),
        ('third_party_payments', 'Third party payments'),
        ('advances', 'Advances')
    ], string="Earn category", default="other_concepts", required=True)

    deduction_category = fields.Selection([
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
    ], string="Deduction category", default="other_deductions", required=True)

    edi_percent_select = fields.Selection([
        ('default', 'Default'),
        ('fix', 'Fixed percent'),
        ('code', 'Python Code'),
    ], string='Percent Type', index=True, required=True, default='default',
        help="The computation method for the rule percent.")
    edi_percent_python_compute = fields.Text(string='Python Code',
                                             default='''
                    # Available variables:
                    #----------------------
                    # payslip: object containing the payslips
                    # employee: hr.employee object
                    # contract: hr.contract object
                    # inputs: object containing the computed inputs.

                    # Note: returned value have to be set in the variable 'percent'

                    result = inputs.example * 0.10''')
    edi_percent_fix = fields.Float(string='Fixed Percent', digits=dp.get_precision('Payroll'), default=0.0)

    edi_is_detailed = fields.Boolean(string="Edi detailed", default=False)

    edi_quantity_select = fields.Selection([
        ('default', 'Default'),
        ('auto', 'Auto')
    ], string='Edi quantity', index=True, required=True, default='default',
        help="The computation method for rule Edi quantity.")

    def compute_edi_percent(self, payslip):
        self.ensure_one()

        class BrowsableObject(object):
            def __init__(self, browsable_dict, env):
                self.dict = browsable_dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        inputs_dict = {}
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        inputs = BrowsableObject(inputs_dict, self.env)
        contract = payslip.contract_id
        employee = contract.employee_id

        local_dict = {'payslip': payslip, 'inputs': inputs, 'employee': employee, 'contract': contract, 'result': None}

        if self.edi_percent_select == 'default':
            if self.amount_select == 'percentage':
                return self.amount_percentage
            else:
                return 100.0
        elif self.edi_percent_select == 'fix':
            return self.edi_percent_fix
        else:
            try:
                safe_eval(self.edi_percent_python_compute, local_dict, mode='exec', nocopy=True)
                return float(local_dict['result'])
            except Exception as e:
                raise UserError(
                    _('Wrong percent python code defined for salary rule %s (%s). %s') % (self.name, self.code, e))
