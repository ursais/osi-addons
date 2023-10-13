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


import ast
import calendar
import json
import logging
from datetime import datetime, timedelta

import requests
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    origin_payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Origin payslip", readonly=True, copy=False,
                                        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    # They allow storing synchronous and production modes used when invoicing
    edi_sync = fields.Boolean(string="Sync", default=False, copy=False)
    edi_is_not_test = fields.Boolean(string="In production", default=False, copy=False)

    # Edi fields
    date = fields.Date('Date Account', states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
                       readonly=True, help="Keep empty to use the period of the validation(Payslip) date.")
    payment_date = fields.Date("Payment date", required=True, readonly=True,
                               states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
                               default=lambda self: fields.Date.to_string(
                                   (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    payment_form_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.payment_forms", string="Payment form", default=1,
                                      readonly=True, copy=True,
                                      states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    payment_method_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.payment_methods", string="Payment method",
                                        default=1, readonly=True, copy=True,
                                        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    accrued_total_amount = fields.Monetary("Accrued", currency_field='currency_id', readonly=True, copy=True)
    deductions_total_amount = fields.Monetary("Deductions", currency_field='currency_id', readonly=True, copy=True)
    others_total_amount = fields.Monetary("Others", currency_field='currency_id', readonly=True, copy=True)
    total_amount = fields.Monetary("Total", currency_field='currency_id', readonly=True, copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=False, compute='_compute_currency')
    earn_ids = fields.One2many('l10n_co_hr_payroll.earn.line', 'payslip_id', string='Earn lines', readonly=True,
                               copy=True, states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    deduction_ids = fields.One2many('l10n_co_hr_payroll.deduction.line', 'payslip_id', string='Deduction lines',
                                    copy=True, readonly=True,
                                    states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    worked_days_total = fields.Integer("Worked days", default=0)

    # Edi response fields
    edi_is_valid = fields.Boolean("Is valid?", copy=False)
    edi_is_restored = fields.Boolean("Is restored?", copy=False)
    edi_algorithm = fields.Char("Algorithm", copy=False)
    edi_class = fields.Char("Class", copy=False)
    edi_number = fields.Char("Number", copy=False)
    edi_uuid = fields.Char("UUID", copy=False)
    edi_issue_date = fields.Date("Date", copy=False)
    edi_issue_datetime = fields.Char(string="Issue datetime", copy=False, readonly=True)
    edi_expedition_date = fields.Char("Expedition date", copy=False)
    edi_zip_key = fields.Char("Zip key", copy=False)
    edi_status_code = fields.Char("Status code", copy=False)
    edi_status_description = fields.Char("Status description", copy=False)
    edi_status_message = fields.Char("Status message", copy=False)
    edi_errors_messages = fields.Char("Error messages", copy=False)
    edi_xml_name = fields.Char("XML name", copy=False)
    edi_zip_name = fields.Char("Zip name", copy=False)
    edi_signature = fields.Char("Signature", copy=False)
    edi_qr_code = fields.Char("QR code", copy=False)
    edi_qr_data = fields.Char("QR data", copy=False)
    edi_qr_link = fields.Char("QR link", copy=False)
    edi_pdf_download_link = fields.Char("PDF link", copy=False)
    edi_xml_base64 = fields.Binary("XML", copy=False)
    edi_application_response_base64 = fields.Binary("Application response", copy=False)
    edi_attached_document_base64 = fields.Binary("Attached document", copy=False)
    edi_pdf_base64 = fields.Binary("PDF", copy=False)
    edi_zip_base64 = fields.Binary("Zip", copy=False)
    edi_type_environment = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_environments",
                                           string="Type environment", copy=False)
    edi_payload = fields.Text("Payload", copy=False)

    edi_payload_html = fields.Html("Html payload", copy=False, compute="_compute_edi_payload_html", store=True)

    payslip_edi_ids = fields.Many2many(comodel_name='hr.payslip.edi', string='Edi Payslips',
                                       relation='hr_payslip_hr_payslip_edi_rel',
                                       readonly=True, copy=False)

    # color = fields.Integer(string='Color', required=False, default=None, readonly=True, compute='_compute_color',
    #                        store=True, copy=False)

    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string='Month', compute='_compute_month', store=True, copy=False)
    year = fields.Integer(string='Year', compute='_compute_year', store=True, copy=False)

    def dian_preview(self):
        for rec in self:
            if rec.edi_uuid:
                return {
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + rec.edi_uuid,
                }

    @api.depends('edi_payload')
    def _compute_edi_payload_html(self):
        hr_payslip_edi_env = self.env['hr.payslip.edi']
        for rec in self:
            if rec.edi_payload:
                try:
                    rec.edi_payload_html = hr_payslip_edi_env.payload2html(json.loads(rec.edi_payload), 2)
                except json.decoder.JSONDecodeError as e:
                    rec.edi_payload_html = hr_payslip_edi_env.payload2html(ast.literal_eval(rec.edi_payload), 2)
            else:
                rec.edi_payload_html = ""

    @api.depends('date_from')
    def _compute_month(self):
        for rec in self:
            rec.month = str(rec.date_from.month) if rec.date_from else None

    @api.depends('date_from')
    def _compute_year(self):
        for rec in self:
            rec.year = rec.date_from.year

    def _format_date_hours(self, date, hours):
        date_hours = datetime(date.year,
                              date.month,
                              date.day) + timedelta(hours=hours)
        return fields.Datetime.to_string(date_hours)

    def _compute_currency(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id

    def compute_sheet(self):
        for rec in self:
            # Read all codes
            all_earn_code_list = []
            for earn_id in rec.earn_ids:
                all_earn_code_list.append(earn_id.code)

            # Read all codes
            all_deduction_code_list = []
            for deduction_id in rec.deduction_ids:
                all_deduction_code_list.append(deduction_id.code)

            # Remove records with codes duplicated
            earn_code_list = []
            [earn_code_list.append(code) for code in all_earn_code_list if code not in earn_code_list]

            # Remove records with codes duplicated
            deduction_code_list = []
            [deduction_code_list.append(x) for x in all_deduction_code_list if x not in deduction_code_list]

            # List of all earn details
            earn_list = []
            for earn_id in rec.earn_ids:
                earn_list.append({
                    'input_type_id': earn_id.rule_input_id.input_type_id.id,
                    'name': earn_id.name,
                    'sequence': earn_id.sequence,
                    'code': earn_id.code,
                    'amount': abs(earn_id.amount),
                    'quantity': abs(earn_id.quantity),
                    'total': abs(earn_id.total),
                    'category': earn_id.category
                })

            # List of all deduction details
            deduction_list = []
            for deduction_id in rec.deduction_ids:
                deduction_list.append({
                    'input_type_id': deduction_id.rule_input_id.input_type_id.id,
                    'name': deduction_id.name,
                    'sequence': deduction_id.sequence,
                    'code': deduction_id.code,
                    'amount': abs(deduction_id.amount)
                })

            # Remove input line records with codes in earn and deduction code list
            input_line_list = []
            for input_line in rec.input_line_ids:
                if (input_line.input_type_id.code in earn_code_list
                        or input_line.input_type_id.code in deduction_code_list):
                    input_line_list.append((2, input_line.id))

            # Remove worked days line records with codes in earn code list
            worked_days_line_list = []
            for worked_days_line in rec.worked_days_line_ids:
                if worked_days_line.work_entry_type_id.code in earn_code_list:
                    worked_days_line_list.append((2, worked_days_line.id))

            # Prepare earn input lines
            for code in earn_code_list:
                filter_list = list(filter(lambda earn_detail: earn_detail["code"] == code, earn_list))
                amount = 0
                quantity = 0
                total = 0
                for filter_item in filter_list:
                    amount += filter_item['amount']
                    quantity += filter_item['quantity']
                    total += filter_item['total']

                res_item = filter_list[0]

                # Prepare input lines
                input_line_list.append((0, 0, {
                    'input_type_id': res_item['input_type_id'],
                    'payslip_id': rec.id,
                    'sequence': res_item['sequence'],
                    'amount': abs(total),
                    'contract_id': rec.contract_id.id
                }))

                # Search or create work entry type for code
                work_entry_type_id = self.env['hr.work.entry.type'].search([('code', '=', code)])
                if not work_entry_type_id and res_item['category'] in (
                        'vacation_common',
                        'vacation_compensated',
                        'licensings_maternity_or_paternity_leaves',
                        'licensings_permit_or_paid_licenses',
                        'licensings_suspension_or_unpaid_leaves',
                        'incapacities_common',
                        'incapacities_professional',
                        'incapacities_working',
                        'legal_strikes',
                        'daily_overtime',
                        'overtime_night_hours',
                        'hours_night_surcharge',
                        'sunday_holiday_daily_overtime',
                        'daily_surcharge_hours_sundays_holidays',
                        'sunday_night_overtime_holidays',
                        'sunday_holidays_night_surcharge_hours'
                ):
                    self.env['hr.work.entry.type'].create({
                        'name': res_item['name'],
                        'code': res_item['code'],
                        'sequence': res_item['sequence'],
                        'round_days': 'NO'
                    })

                work_entry_type_id = self.env['hr.work.entry.type'].search([('code', '=', code)])
                if work_entry_type_id:
                    work_entry_type_id = work_entry_type_id[0]

                # Prepare worked days lines
                if res_item['category'] in (
                        'vacation_common',
                        'vacation_compensated',
                        'licensings_maternity_or_paternity_leaves',
                        'licensings_permit_or_paid_licenses',
                        'licensings_suspension_or_unpaid_leaves',
                        'incapacities_common',
                        'incapacities_professional',
                        'incapacities_working',
                        'legal_strikes'
                ):
                    worked_days_line_list.append((0, 0, {
                        'work_entry_type_id': work_entry_type_id.id,
                        'name': res_item['name'],
                        'payslip_id': rec.id,
                        'sequence': res_item['sequence'],
                        'number_of_days': abs(quantity),
                        'number_of_hours': 0,
                        'contract_id': rec.contract_id.id
                    }))
                elif res_item['category'] in (
                        'daily_overtime',
                        'overtime_night_hours',
                        'hours_night_surcharge',
                        'sunday_holiday_daily_overtime',
                        'daily_surcharge_hours_sundays_holidays',
                        'sunday_night_overtime_holidays',
                        'sunday_holidays_night_surcharge_hours'
                ):
                    worked_days_line_list.append((0, 0, {
                        'work_entry_type_id': work_entry_type_id.id,
                        'name': res_item['name'],
                        'payslip_id': rec.id,
                        'sequence': res_item['sequence'],
                        'number_of_days': 0,
                        'number_of_hours': abs(quantity),
                        'contract_id': rec.contract_id.id
                    }))

            # Prepare deduction input lines
            for code in deduction_code_list:
                filter_list = list(filter(lambda deduction_detail: deduction_detail["code"] == code, deduction_list))
                amount = 0
                for filter_item in filter_list:
                    amount += filter_item['amount']

                res_item = filter_list[0]

                input_line_list.append((0, 0, {
                    'input_type_id': res_item['input_type_id'],
                    'payslip_id': rec.id,
                    'sequence': res_item['sequence'],
                    'amount': -abs(amount),
                    'contract_id': rec.contract_id.id
                }))

            # Add lines
            rec.update({'input_line_ids': input_line_list})
            rec.update({'worked_days_line_ids': worked_days_line_list})

            # Sequences
            if not rec.number:
                rec.number = _('New')

        res = super(HrPayslip, self).compute_sheet()
        self.compute_totals()

        # The sheet and the totals are calculated again,
        # just in case the totals obtained initially are used to calculate some salary rule.
        # Especially the field worked_days_total
        try:
            if int(self.env['ir.config_parameter'].sudo().get_param('jorels.payroll.recompute_sheet', 1)):
                res = super(HrPayslip, self).compute_sheet()
                self.compute_totals()
        except ValueError as e:
            raise UserError("The system parameter 'jorels.payroll.recompute_sheet' is misconfigured. Use only 0 or 1")

        return res

    def compute_totals(self):
        for rec in self:
            # The date is the sending date
            rec.date = fields.Date.context_today(self)

            # Totals
            accrued_total_amount = 0
            deductions_total_amount = 0
            others_total_amount = 0

            for line_id in rec.line_ids:
                if line_id.salary_rule_id.type_concept == 'earn':
                    if line_id.salary_rule_id.earn_category not in (
                            'licensings_suspension_or_unpaid_leaves',
                            'legal_strikes'
                    ):
                        accrued_total_amount += abs(line_id.total)
                elif line_id.salary_rule_id.type_concept == 'deduction':
                    deductions_total_amount += abs(line_id.total)
                elif line_id.salary_rule_id.type_concept == 'other':
                    others_total_amount += abs(line_id.total)

            rec.accrued_total_amount = accrued_total_amount
            rec.deductions_total_amount = deductions_total_amount
            rec.others_total_amount = others_total_amount
            rec.total_amount = accrued_total_amount - deductions_total_amount

            rec.edi_payload = json.dumps(rec.get_json_request(), indent=4, sort_keys=False)

    @api.model
    def calculate_time_worked(self, start, end):
        if end < start:
            raise ValidationError(_("The time worked cannot be negative."))

        end_day = 30 if end.day == calendar.monthrange(end.year, end.month)[1] else end.day
        start_day = 30 if start.day == calendar.monthrange(start.year, start.month)[1] else start.day

        return (end.year - start.year) * 360 + (end.month - start.month) * 30 + end_day - start_day + 1

    def get_json_request(self):
        for rec in self:
            # Force compute edi payroll period
            rec.contract_id._compute_payroll_period_id()

            if not rec.number:
                raise UserError(_("The payroll must have a consecutive number, 'Reference' field"))
            if not rec.contract_id.payroll_period_id:
                raise UserError(_("The contract must have the 'Scheduled Pay' field configured"))
            if not rec.company_id.name:
                raise UserError(_("Your company does not have a name"))
            if not rec.company_id.type_document_identification_id:
                raise UserError(_("Your company does not have an identification type"))
            if not rec.company_id.vat:
                raise UserError(_("Your company does not have a document number"))
            if not rec.company_id.partner_id.postal_municipality_id:
                raise UserError(_("Your company does not have a postal municipality"))
            if not rec.company_id.street:
                raise UserError(_("Your company does not have an address"))
            if not rec.contract_id.type_worker_id:
                raise UserError(_("The contract must have the 'Type worker' field configured"))
            if not rec.contract_id.subtype_worker_id:
                raise UserError(_("The contract must have the 'Subtype worker' field configured"))
            if not rec.employee_id.address_home_id.first_name:
                raise UserError(_("Employee does not have a first name"))
            if not rec.employee_id.address_home_id.surname:
                raise UserError(_("Employee does not have a surname"))
            if not rec.employee_id.address_home_id.type_document_identification_id:
                raise UserError(_("Employee does not have an identification type"))
            if rec.employee_id.address_home_id.type_document_identification_id.id == 6:
                raise UserError(_("The employee's document type cannot be NIT"))
            if not rec.employee_id.address_home_id.vat:
                raise UserError(_("Employee does not have an document number"))
            if not rec.employee_id.address_home_id.postal_municipality_id:
                raise UserError(_("Employee does not have a postal municipality"))
            if not rec.employee_id.address_home_id.street:
                raise UserError(_("Employee does not have an address."))
            if not rec.contract_id.name:
                raise UserError(_("Contract does not have a name"))
            if rec.contract_id.wage <= 0:
                raise UserError(_("The contract must have the 'Wage' field configured"))
            if not rec.contract_id.type_contract_id:
                raise UserError(_("The contract must have the 'Type contract' field configured"))
            if not rec.contract_id.date_start:
                raise UserError(_("The contract must have the 'Start Date' field configured"))
            if not rec.date_from:
                raise UserError(_("The payroll must have a period"))
            if not rec.date_to:
                raise UserError(_("The payroll must have a period"))
            if not rec.payment_form_id:
                raise UserError(_("The payroll must have a payment form"))
            if not rec.payment_method_id:
                raise UserError(_("The payroll must have a payment method"))
            if not rec.payment_date:
                raise UserError(_("The payroll must have a payment date"))

            rec.edi_sync = rec.company_id.edi_payroll_is_not_test

            sequence = {}
            if rec.number and rec.number not in ('New', _('New')):
                sequence_number = ''.join([i for i in rec.number if i.isdigit()])
                sequence_prefix = rec.number.split(sequence_number)
                if sequence_prefix:
                    sequence = {
                        # "worker_code": "string",
                        "prefix": sequence_prefix[0],
                        "number": int(sequence_number)
                    }
                else:
                    raise UserError(_("The sequence must have a prefix"))

            information = {
                "payroll_period_code": rec.contract_id.payroll_period_id.id,
                "currency_code": 35,
                # "trm": 1
            }

            employer_id_code = rec.company_id.type_document_identification_id.id
            employer_id_number_general = ''.join([i for i in rec.company_id.vat if i.isdigit()])
            if employer_id_code == 6:
                employer_id_number = employer_id_number_general[:-1]
            else:
                employer_id_number = employer_id_number_general

            employer = {
                "name": rec.company_id.name,
                # "surname": "string",
                # "second_surname": "string",
                # "first_name": "string",
                # "other_names": "string",
                "id_code": employer_id_code,
                "id_number": employer_id_number,
                "country_code": 46,
                "municipality_code": rec.company_id.partner_id.postal_municipality_id.id,
                "address": rec.company_id.street
            }

            employee = {
                "type_worker_code": rec.contract_id.type_worker_id.id,
                "subtype_worker_code": rec.contract_id.subtype_worker_id.id,
                "high_risk_pension": rec.contract_id.high_risk_pension,
                "id_code": rec.employee_id.address_home_id.type_document_identification_id.id,
                "id_number": ''.join([i for i in rec.employee_id.address_home_id.vat if i.isdigit()]),
                "surname": rec.employee_id.address_home_id.surname,
                "first_name": rec.employee_id.address_home_id.first_name,
                "country_code": 46,
                "municipality_code": rec.employee_id.address_home_id.postal_municipality_id.id,
                "address": rec.employee_id.address_home_id.street,
                "integral_salary": rec.contract_id.integral_salary,
                "contract_code": rec.contract_id.type_contract_id.id,
                "salary": abs(rec.contract_id.wage),
                # "worker_code": "string"
            }
            if rec.employee_id.address_home_id.other_names:
                employee['other_names'] = rec.employee_id.address_home_id.other_names
            if rec.employee_id.address_home_id.second_surname:
                employee['second_surname'] = rec.employee_id.address_home_id.second_surname

            if rec.contract_id.date_end:
                amount_time = self.calculate_time_worked(rec.contract_id.date_start, rec.contract_id.date_end)
            else:
                amount_time = self.calculate_time_worked(rec.contract_id.date_start, rec.date_to)

            rec.date = fields.Date.context_today(rec)

            period = {
                "admission_date": fields.Date.to_string(rec.contract_id.date_start),
                "settlement_start_date": fields.Date.to_string(rec.date_from),
                "settlement_end_date": fields.Date.to_string(rec.date_to),
                "amount_time": amount_time,
                "date_issue": fields.Date.to_string(rec.date)
            }
            if rec.contract_id.date_end:
                period['withdrawal_date'] = fields.Date.to_string(rec.contract_id.date_end)

            payment = {
                "code": rec.payment_form_id.id,
                "method_code": rec.payment_method_id.id,
                # "bank": "string",
                # "account_type": "string",
                # "account_number": "string"
            }

            # Earn details
            basic = {}
            company_withdrawal_bonus = 0
            compensation = 0
            endowment = 0
            layoffs = {}
            primas = {}
            refund = 0
            sustainment_support = 0
            telecommuting = 0

            advances = []
            assistances = []
            bonuses = []
            commissions = []
            compensations = []
            overtimes_surcharges = []
            incapacities = []
            legal_strikes = []
            licensings_maternity_or_paternity_leaves = []
            licensings_permit_or_paid_licenses = []
            licensings_suspension_or_unpaid_leaves = []
            other_concepts = []
            third_party_payments = []
            transports = []
            vacation_common = []
            vacation_compensated = []
            vouchers = []

            # Earn details iteration
            for earn_id in rec.earn_ids:
                if not earn_id.rule_input_id.input_id.edi_is_detailed:
                    raise UserError(_("This concept must be calculated through the salary rules: %s")
                                    % earn_id.rule_input_id.input_id.name)

                if earn_id.category in (
                        'basic',
                        'company_withdrawal_bonus',
                        'compensation',
                        'endowment',
                        'layoffs',
                        'layoffs_interest',
                        'primas',
                        'primas_non_salary',
                        'refund',
                        'sustainment_support',
                        'telecommuting'
                ):
                    raise UserError(_("This concept must be configured in salary rules as not detailed: %s")
                                    % earn_id.rule_input_id.input_id.name)

                if earn_id.category == 'advances':
                    if earn_id.total:
                        advances.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'assistances':
                    if earn_id.total:
                        assistances.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'assistances_non_salary':
                    if earn_id.total:
                        assistances.append({
                            "non_salary_payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'bonuses':
                    if earn_id.total:
                        bonuses.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'bonuses_non_salary':
                    if earn_id.total:
                        bonuses.append({
                            "non_salary_payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'commissions':
                    if earn_id.total:
                        commissions.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'compensations_extraordinary':
                    if earn_id.total:
                        compensations.append({
                            "extraordinary": abs(earn_id.total)
                        })
                elif earn_id.category == 'compensations_ordinary':
                    if earn_id.total:
                        compensations.append({
                            "ordinary": abs(earn_id.total)
                        })
                elif earn_id.category == 'daily_overtime':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 1,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'daily_surcharge_hours_sundays_holidays':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 5,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'hours_night_surcharge':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 3,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'incapacities_common':
                    if earn_id.quantity and earn_id.total:
                        incapacities.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "incapacity_code": 1,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'incapacities_professional':
                    if earn_id.quantity and earn_id.total:
                        incapacities.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "incapacity_code": 2,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'incapacities_working':
                    if earn_id.quantity and earn_id.total:
                        incapacities.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "incapacity_code": 3,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'legal_strikes':
                    if earn_id.quantity:
                        legal_strikes.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                        })
                elif earn_id.category == 'licensings_maternity_or_paternity_leaves':
                    if earn_id.quantity and earn_id.total:
                        licensings_maternity_or_paternity_leaves.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'licensings_permit_or_paid_licenses':
                    if earn_id.quantity and earn_id.total:
                        licensings_permit_or_paid_licenses.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'licensings_suspension_or_unpaid_leaves':
                    if earn_id.quantity:
                        licensings_suspension_or_unpaid_leaves.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity)
                        })
                elif earn_id.category == 'other_concepts':
                    if earn_id.total:
                        other_concepts.append({
                            "description": earn_id.name,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'other_concepts_non_salary':
                    if earn_id.total:
                        other_concepts.append({
                            "description": earn_id.name,
                            "non_salary_payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'overtime_night_hours':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 2,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'sunday_holiday_daily_overtime':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 4,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'sunday_holidays_night_surcharge_hours':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 7,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'sunday_night_overtime_holidays':
                    if earn_id.quantity and earn_id.total:
                        overtimes_surcharges.append({
                            "start": self._format_date_hours(earn_id.date_start, earn_id.time_start),
                            "end": self._format_date_hours(earn_id.date_end, earn_id.time_end),
                            "quantity": abs(earn_id.quantity),
                            "time_code": 6,
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'third_party_payments':
                    if earn_id.total:
                        third_party_payments.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'transports_assistance':
                    if earn_id.total:
                        transports.append({
                            "assistance": abs(earn_id.total)
                        })
                elif earn_id.category == 'transports_non_salary_viatic':
                    if earn_id.total:
                        transports.append({
                            "non_salary_viatic": abs(earn_id.total)
                        })
                elif earn_id.category == 'transports_viatic':
                    if earn_id.total:
                        transports.append({
                            "viatic": abs(earn_id.total)
                        })
                elif earn_id.category == 'vacation_common':
                    if earn_id.quantity and earn_id.total:
                        vacation_common.append({
                            "start": fields.Date.to_string(earn_id.date_start),
                            "end": fields.Date.to_string(earn_id.date_end),
                            "quantity": abs(earn_id.quantity),
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'vacation_compensated':
                    if earn_id.quantity and earn_id.total:
                        vacation_compensated.append({
                            "quantity": abs(earn_id.quantity),
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'vouchers':
                    if earn_id.total:
                        vouchers.append({
                            "payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'vouchers_non_salary':
                    if earn_id.total:
                        vouchers.append({
                            "non_salary_payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'vouchers_non_salary_food':
                    if earn_id.total:
                        vouchers.append({
                            "non_salary_food_payment": abs(earn_id.total)
                        })
                elif earn_id.category == 'vouchers_salary_food':
                    if earn_id.total:
                        vouchers.append({
                            "salary_food_payment": abs(earn_id.total)
                        })

            # Deduction details
            deduction_afc = 0
            deduction_complementary_plans = 0
            deduction_cooperative = 0
            deduction_debt = 0
            deduction_education = 0
            deduction_health = {}
            deduction_pension_fund = {}
            deduction_pension_security_fund = {}
            deduction_refund = 0
            deduction_sanctions = {}
            deduction_tax_lien = 0
            deduction_trade_unions = {}
            deduction_voluntary_pension = 0
            deduction_withholding_source = 0

            deduction_advances = []
            deduction_libranzas = []
            deduction_others = []
            deduction_third_party_payments = []

            # Deduction details iteration
            for deduction_id in rec.deduction_ids:
                if not deduction_id.rule_input_id.input_id.edi_is_detailed:
                    raise UserError(_("This concept must be calculated through the salary rules: %s")
                                    % deduction_id.rule_input_id.input_id.name)

                # For trade unions and sanctions this settings is temporary
                if deduction_id.category in (
                        'afc',
                        'complementary_plans',
                        'cooperative',
                        'debt',
                        'education',
                        'health',
                        'pension_fund',
                        'pension_security_fund',
                        'pension_security_fund_subsistence',
                        'refund',
                        'sanctions_private',
                        'sanctions_public',
                        'tax_lien',
                        'trade_unions',
                        'voluntary_pension',
                        'withholding_source'
                ):
                    raise UserError(_("This concept must be configured in salary rules as not detailed: %s")
                                    % deduction_id.rule_input_id.input_id.name)
                elif deduction_id.category == 'advances':
                    if deduction_id.amount:
                        deduction_advances.append({
                            "payment": abs(deduction_id.amount)
                        })
                elif deduction_id.category == 'libranzas':
                    if deduction_id.amount:
                        deduction_libranzas.append({
                            "description": deduction_id.name,
                            "payment": abs(deduction_id.amount)
                        })
                elif deduction_id.category == 'other_deductions':
                    if deduction_id.amount:
                        deduction_others.append({
                            "payment": abs(deduction_id.amount)
                        })
                elif deduction_id.category == 'third_party_payments':
                    if deduction_id.amount:
                        deduction_third_party_payments.append({
                            "payment": abs(deduction_id.amount)
                        })

            # Salary computation iteration
            for line_id in rec.line_ids:
                line_id.edi_rate = line_id.compute_edi_rate()
                line_id.edi_quantity = line_id.compute_edi_quantity()
                if line_id.salary_rule_id.type_concept == 'earn' and not line_id.salary_rule_id.edi_is_detailed:
                    if line_id.salary_rule_id.earn_category == 'basic':
                        if line_id.total:
                            # The days worked are calculated at the end
                            basic['worked_days'] = None
                            basic['worker_salary'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'company_withdrawal_bonus':
                        if line_id.total:
                            company_withdrawal_bonus = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'compensation':
                        if line_id.total:
                            compensation = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'endowment':
                        if line_id.total:
                            endowment = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'layoffs':
                        if line_id.total:
                            layoffs['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'layoffs_interest':
                        if line_id.total:
                            layoffs['percentage'] = abs(line_id.edi_rate)
                            layoffs['interest_payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'primas':
                        if line_id.total:
                            primas['quantity'] = abs(line_id.edi_quantity)
                            primas['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'primas_non_salary':
                        if line_id.total:
                            primas['non_salary_payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'refund':
                        if line_id.total:
                            refund = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'sustainment_support':
                        if line_id.total:
                            sustainment_support = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'telecommuting':
                        if line_id.total:
                            telecommuting = abs(line_id.total)
                    elif line_id.salary_rule_id.earn_category == 'advances':
                        if line_id.total:
                            advances.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'assistances':
                        if line_id.total:
                            assistances.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'assistances_non_salary':
                        if line_id.total:
                            assistances.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'bonuses':
                        if line_id.total:
                            bonuses.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'bonuses_non_salary':
                        if line_id.total:
                            bonuses.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'commissions':
                        if line_id.total:
                            commissions.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'compensations_extraordinary':
                        if line_id.total:
                            compensations.append({
                                "extraordinary": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'compensations_ordinary':
                        if line_id.total:
                            compensations.append({
                                "ordinary": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'daily_overtime':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 1,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'daily_surcharge_hours_sundays_holidays':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 5,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'hours_night_surcharge':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 3,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_common':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 1,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_professional':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 2,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'incapacities_working':
                        if line_id.edi_quantity and line_id.total:
                            incapacities.append({
                                "quantity": abs(line_id.edi_quantity),
                                "incapacity_code": 3,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'legal_strikes':
                        if line_id.edi_quantity:
                            legal_strikes.append({
                                "quantity": abs(line_id.edi_quantity)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_maternity_or_paternity_leaves':
                        if line_id.edi_quantity and line_id.total:
                            licensings_maternity_or_paternity_leaves.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_permit_or_paid_licenses':
                        if line_id.edi_quantity and line_id.total:
                            licensings_permit_or_paid_licenses.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'licensings_suspension_or_unpaid_leaves':
                        if line_id.edi_quantity:
                            licensings_suspension_or_unpaid_leaves.append({
                                "quantity": abs(line_id.edi_quantity)
                            })
                    elif line_id.salary_rule_id.earn_category == 'other_concepts':
                        if line_id.total:
                            other_concepts.append({
                                "description": line_id.name,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'other_concepts_non_salary':
                        if line_id.total:
                            other_concepts.append({
                                "description": line_id.name,
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'overtime_night_hours':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 2,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_holiday_daily_overtime':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 4,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_holidays_night_surcharge_hours':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 7,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'sunday_night_overtime_holidays':
                        if line_id.edi_quantity and line_id.total:
                            overtimes_surcharges.append({
                                "quantity": abs(line_id.edi_quantity),
                                "time_code": 6,
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'third_party_payments':
                        if line_id.total:
                            third_party_payments.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_assistance':
                        if line_id.total:
                            transports.append({
                                'assistance': abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_non_salary_viatic':
                        if line_id.total:
                            transports.append({
                                "non_salary_viatic": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'transports_viatic':
                        if line_id.total:
                            transports.append({
                                "viatic": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vacation_common':
                        if line_id.edi_quantity and line_id.total:
                            vacation_common.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vacation_compensated':
                        if line_id.edi_quantity and line_id.total:
                            vacation_compensated.append({
                                "quantity": abs(line_id.edi_quantity),
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers':
                        if line_id.total:
                            vouchers.append({
                                "payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_non_salary':
                        if line_id.total:
                            vouchers.append({
                                "non_salary_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_non_salary_food':
                        if line_id.total:
                            vouchers.append({
                                "non_salary_food_payment": abs(line_id.total)
                            })
                    elif line_id.salary_rule_id.earn_category == 'vouchers_salary_food':
                        if line_id.total:
                            vouchers.append({
                                "salary_food_payment": abs(line_id.total)
                            })
                elif line_id.salary_rule_id.type_concept == 'deduction' \
                        and not line_id.salary_rule_id.edi_is_detailed \
                        and line_id.total:
                    if line_id.salary_rule_id.deduction_category == 'afc':
                        deduction_afc = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'complementary_plans':
                        deduction_complementary_plans = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'cooperative':
                        deduction_cooperative = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'debt':
                        deduction_debt = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'education':
                        deduction_education = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'health':
                        deduction_health['percentage'] = abs(line_id.edi_rate)
                        deduction_health['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_fund':
                        deduction_pension_fund['percentage'] = abs(line_id.edi_rate)
                        deduction_pension_fund['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_security_fund':
                        deduction_pension_security_fund['percentage'] = abs(line_id.edi_rate)
                        deduction_pension_security_fund['payment'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'pension_security_fund_subsistence':
                        deduction_pension_security_fund['percentage_subsistence'] = abs(line_id.edi_rate)
                        deduction_pension_security_fund['payment_subsistence'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'refund':
                        deduction_refund = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'sanctions_private':
                        deduction_sanctions['payment_private'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'sanctions_public':
                        deduction_sanctions['payment_public'] = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'tax_lien':
                        deduction_tax_lien = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'trade_unions':
                        deduction_trade_unions = {
                            'percentage': abs(line_id.edi_rate),
                            'payment': abs(line_id.total)
                        }
                    elif line_id.salary_rule_id.deduction_category == 'voluntary_pension':
                        deduction_voluntary_pension = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'withholding_source':
                        deduction_withholding_source = abs(line_id.total)
                    elif line_id.salary_rule_id.deduction_category == 'advances':
                        deduction_advances.append({
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'libranzas':
                        deduction_libranzas.append({
                            "description": line_id.salary_rule_id.name,
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'other_deductions':
                        deduction_others.append({
                            "payment": abs(line_id.total)
                        })
                    elif line_id.salary_rule_id.deduction_category == 'third_party_payments':
                        deduction_third_party_payments.append({
                            "payment": abs(line_id.total)
                        })

            # Calculate days worked
            rec.worked_days_total = self.calculate_time_worked(rec.date_from, rec.date_to)
            for list_with_days in [
                vacation_common,
                licensings_maternity_or_paternity_leaves,
                licensings_permit_or_paid_licenses,
                licensings_suspension_or_unpaid_leaves,
                incapacities,
                legal_strikes
            ]:
                for dict_with_days in list_with_days:
                    rec.worked_days_total -= dict_with_days['quantity']
            if rec.worked_days_total < 0:
                rec.worked_days_total = 0
            basic['worked_days'] = rec.worked_days_total

            if 'worker_salary' not in basic:
                basic['worker_salary'] = 0.0

            # Complete json request
            earn = {
                "basic": basic
            }

            # Earn details
            vacation = {}
            if vacation_common:
                vacation['common'] = vacation_common
            if vacation_compensated:
                vacation['compensated'] = vacation_compensated
            if vacation:
                earn['vacation'] = vacation

            if primas:
                if 'payment' in primas:
                    earn['primas'] = primas
                else:
                    raise UserError(_("The 'Primas' rule is mandatory in order to report Primas"))

            if layoffs:
                if ('payment' in layoffs) and ('interest_payment' in layoffs):
                    earn['layoffs'] = layoffs
                else:
                    raise UserError(
                        _("The 'Layoffs' and 'Layoffs interest' rules are mandatory in order to report Layoffs"))

            licensings = {}
            if licensings_maternity_or_paternity_leaves:
                licensings['licensings_maternity_or_paternity_leaves'] = licensings_maternity_or_paternity_leaves
            if licensings_permit_or_paid_licenses:
                licensings['licensings_permit_or_paid_licenses'] = licensings_permit_or_paid_licenses
            if licensings_suspension_or_unpaid_leaves:
                licensings['licensings_suspension_or_unpaid_leaves'] = licensings_suspension_or_unpaid_leaves
            if licensings:
                earn['licensings'] = licensings

            if endowment:
                earn['endowment'] = endowment

            if sustainment_support:
                earn['sustainment_support'] = sustainment_support

            if telecommuting:
                earn['telecommuting'] = telecommuting

            if company_withdrawal_bonus:
                earn['company_withdrawal_bonus'] = company_withdrawal_bonus

            if compensation:
                earn['compensation'] = compensation

            if refund:
                earn['refund'] = refund

            if transports:
                earn['transports'] = transports

            if overtimes_surcharges:
                earn['overtimes_surcharges'] = overtimes_surcharges

            if incapacities:
                earn['incapacities'] = incapacities

            if bonuses:
                earn['bonuses'] = bonuses

            if assistances:
                earn['assistances'] = assistances

            if legal_strikes:
                earn['legal_strikes'] = legal_strikes

            if other_concepts:
                earn['other_concepts'] = other_concepts

            if compensations:
                earn['compensations'] = compensations

            if vouchers:
                earn['vouchers'] = vouchers

            if commissions:
                earn['commissions'] = commissions

            if third_party_payments:
                earn['third_party_payments'] = third_party_payments

            if advances:
                earn['advances'] = advances

            # Deduction details
            deduction = {}

            if deduction_health:
                deduction['health'] = deduction_health

            if deduction_pension_fund:
                deduction['pension_fund'] = deduction_pension_fund

            if deduction_pension_security_fund:
                deduction['pension_security_fund'] = deduction_pension_security_fund

            if deduction_voluntary_pension:
                deduction['voluntary_pension'] = deduction_voluntary_pension

            if deduction_withholding_source:
                deduction['withholding_source'] = deduction_withholding_source

            if deduction_afc:
                deduction['afc'] = deduction_afc

            if deduction_cooperative:
                deduction['cooperative'] = deduction_cooperative

            if deduction_tax_lien:
                deduction['tax_lien'] = deduction_tax_lien

            if deduction_complementary_plans:
                deduction['complementary_plans'] = deduction_complementary_plans

            if deduction_education:
                deduction['education'] = deduction_education

            if deduction_refund:
                deduction['refund'] = deduction_refund

            if deduction_debt:
                deduction['debt'] = deduction_debt

            if deduction_trade_unions:
                deduction['trade_unions'] = [deduction_trade_unions]

            if deduction_sanctions:
                if 'payment_public' not in deduction_sanctions:
                    deduction_sanctions['payment_public'] = 0.0
                if 'payment_private' not in deduction_sanctions:
                    deduction_sanctions['payment_private'] = 0.0
                deduction['sanctions'] = [deduction_sanctions]

            if deduction_libranzas:
                deduction['libranzas'] = deduction_libranzas

            if deduction_third_party_payments:
                deduction['third_party_payments'] = deduction_third_party_payments

            if deduction_advances:
                deduction['advances'] = deduction_advances

            if deduction_others:
                deduction['other_deductions'] = deduction_others

            # Payment
            payment_dates = [{
                "date": fields.Date.to_string(rec.payment_date)
            }]

            json_request = {}
            json_request['sync'] = rec.edi_sync
            # json_request["rounding"] = 0
            json_request['accrued_total'] = rec.accrued_total_amount
            json_request['deductions_total'] = rec.deductions_total_amount
            json_request['total'] = rec.total_amount
            if sequence:
                json_request['sequence'] = sequence
            json_request['information'] = information
            # json_request["novelty"] = novelty
            # json_request["provider"] = provider
            json_request['employer'] = employer
            json_request['employee'] = employee
            json_request['period'] = period
            json_request['payment'] = payment
            json_request['payment_dates'] = payment_dates
            json_request['earn'] = earn

            # Optionals
            if deduction:
                json_request['deduction'] = deduction

            if rec.note:
                notes = [{
                    "text": rec.note
                }]
                json_request['notes'] = notes

            # Credit note
            if rec.credit_note:
                if rec.origin_payslip_id:
                    if rec.origin_payslip_id.edi_is_valid:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.edi_number,
                            'uuid': rec.origin_payslip_id.edi_uuid,
                            'issue_date': str(rec.origin_payslip_id.edi_issue_date)
                        }
                    else:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.number,
                            'issue_date': str(rec.origin_payslip_id.date)
                        }
                else:
                    raise UserError(_("The Origin payslip is required for adjusment notes."))

                json_request = rec.get_json_delete_request(json_request)

            return json_request

    def write_response(self, response, payload):
        for rec in self:
            rec.edi_is_valid = response['is_valid']
            rec.edi_is_restored = response['is_restored']
            rec.edi_algorithm = response['algorithm']
            rec.edi_class = response['class']
            rec.edi_number = response['number']
            rec.edi_uuid = response['uuid']
            rec.edi_issue_date = response['issue_date']
            rec.edi_issue_datetime = response['issue_date']
            rec.edi_expedition_date = response['expedition_date']
            rec.edi_zip_key = response['zip_key']
            rec.edi_status_code = response['status_code']
            rec.edi_status_description = response['status_description']
            rec.edi_status_message = response['status_message']
            rec.edi_errors_messages = str(response['errors_messages'])
            rec.edi_xml_name = response['xml_name']
            rec.edi_zip_name = response['zip_name']
            rec.edi_signature = response['signature']
            rec.edi_qr_code = response['qr_code']
            rec.edi_qr_data = response['qr_data']
            rec.edi_qr_link = response['qr_link']
            rec.edi_pdf_download_link = response['pdf_download_link']
            rec.edi_xml_base64 = response['xml_base64_bytes']
            rec.edi_application_response_base64 = response['application_response_base64_bytes']
            rec.edi_attached_document_base64 = response['attached_document_base64_bytes']
            rec.edi_pdf_base64 = response['pdf_base64_bytes']
            rec.edi_zip_base64 = response['zip_base64_bytes']
            rec.edi_type_environment = response['type_environment_id']
            rec.edi_payload = payload

    @api.model
    def get_json_delete_request(self, requests_data):
        requests_delete = {}

        if 'sequence' in requests_data:
            requests_delete['sequence'] = requests_data['sequence']
        if 'payroll_reference' in requests_data:
            requests_delete['payroll_reference'] = requests_data['payroll_reference']

        requests_delete['sync'] = requests_data['sync']
        requests_delete['information'] = requests_data['information']
        requests_delete['employer'] = requests_data['employer']

        if 'rounding' in requests_data:
            requests_delete['rounding'] = requests_data['rounding']
        if 'provider' in requests_data:
            requests_delete['provider'] = requests_data['provider']
        if 'notes' in requests_data:
            requests_delete['notes'] = requests_data['notes']

        return requests_delete

    def validate_dian_generic(self):
        for rec in self:
            try:
                if not rec.company_id.edi_payroll_enable or rec.company_id.edi_payroll_consolidated_enable:
                    continue

                requests_data = rec.get_json_request()

                if 'sequence' not in requests_data:
                    raise UserError(_("The sequence is required."))

                # Credit note
                if rec.credit_note:
                    type_edi_document = 'payroll_delete'
                    if 'payroll_reference' not in requests_data or 'uuid' not in requests_data['payroll_reference']:
                        raise UserError(_("The reference payroll is not valid."))
                else:
                    type_edi_document = 'payroll'

                # Payload
                payload = json.dumps(requests_data, indent=2, sort_keys=False)

                # Software id and pin
                if rec.company_id.edi_payroll_id and rec.company_id.edi_payroll_pin:
                    requests_data['environment'] = {
                        'software': rec.company_id.edi_payroll_id,
                        'pin': rec.company_id.edi_payroll_pin
                    }
                else:
                    raise UserError(_("You do not have a software id and pin configured"))

                # API key and URL
                if rec.company_id.api_key:
                    token = rec.company_id.api_key
                else:
                    raise UserError(_("You must configure a token"))

                api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                           'https://edipo.jorels.com')
                params = {'token': token}
                header = {"accept": "application/json", "Content-Type": "application/json"}

                # Request
                api_url = api_url + "/" + type_edi_document

                rec.edi_is_not_test = rec.company_id.edi_payroll_is_not_test

                if not rec.edi_is_not_test:
                    if rec.company_id.edi_payroll_test_set_id:
                        params['test_set_id'] = rec.company_id.edi_payroll_test_set_id
                    else:
                        raise UserError(_("You have not configured a 'TestSetId'."))

                _logger.debug('API URL: %s', api_url)
                _logger.debug("DIAN Validation Request: %s", json.dumps(requests_data, indent=2, sort_keys=False))
                # raise Warning(json.dumps(requests_data, indent=2, sort_keys=False))

                response = requests.post(api_url,
                                         json.dumps(requests_data),
                                         headers=header,
                                         params=params).json()
                _logger.debug('API Response: %s', response)

                if 'detail' in response:
                    raise UserError(response['detail'])
                if 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        raise UserError(_("Authentication error with the API"))
                    else:
                        if 'errors' in response:
                            raise UserError(response['message'] + '/ errors: ' + str(response['errors']))
                        else:
                            raise UserError(response['message'])
                elif 'is_valid' in response:
                    rec.write_response(response, payload)
                    if response['is_valid']:
                        # self.env.user.notify_success(message=_("The validation at DIAN has been successful."))
                        _logger.debug("The validation at DIAN has been successful.")
                    elif 'zip_key' in response:
                        if response['zip_key'] is not None:
                            if not rec.edi_is_not_test:
                                # self.env.user.notify_success(message=_("Document sent to DIAN in habilitation."))
                                _logger.debug("Document sent to DIAN in habilitation.")
                            else:
                                temp_message = {rec.edi_status_message, rec.edi_errors_messages,
                                                rec.edi_status_description, rec.edi_status_code}
                                raise UserError(str(temp_message))
                        else:
                            raise UserError(_('A valid Zip key was not obtained. Try again.'))
                    else:
                        raise UserError(_('The document could not be validated in DIAN.'))
                else:
                    raise UserError(_("No logical response was obtained from the API."))
            except Exception as e:
                _logger.debug("Failed to process the request: %s", e)
                raise UserError(_("Failed to process the request: %s") % e)

    def action_payslip_done(self):
        for rec in self:
            if not rec.number or rec.number in ('New', _('New')):
                if rec.credit_note:
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip.note')
                    if not rec.number:
                        raise UserError(
                            _("You must create a sequence for adjusment notes with code 'salary.slip.note'"))
                else:
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip')

        res = super(HrPayslip, self).action_payslip_done()

        for rec in self:
            if rec.company_id.edi_payroll_enable and not rec.company_id.edi_payroll_consolidated_enable:
                rec.validate_dian_generic()

        return res

    def status_zip(self):
        for rec in self:
            try:
                if not rec.company_id.edi_payroll_enable or rec.company_id.edi_payroll_consolidated_enable:
                    continue

                # This line ensures that the electronic fields of the payroll are updated in Odoo, before the request
                payload = json.dumps(rec.get_json_request(), indent=2, sort_keys=False)

                _logger.debug('Payload: %s', payload)

                if rec.edi_zip_key or rec.edi_uuid:
                    requests_data = {}
                    _logger.debug('API Requests: %s', requests_data)

                    # API key and URL
                    if rec.company_id.api_key:
                        token = rec.company_id.api_key
                    else:
                        raise UserError(_("You must configure a token"))

                    api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                               'https://edipo.jorels.com')
                    params = {
                        'token': token,
                        'environment': rec.edi_type_environment.id
                    }
                    header = {"accept": "application/json", "Content-Type": "application/json"}

                    # Request
                    if rec.edi_zip_key:
                        api_url = api_url + "/zip/" + rec.edi_zip_key
                    else:
                        api_url = api_url + "/document/" + rec.edi_uuid

                    _logger.debug('API URL: %s', api_url)

                    response = requests.post(api_url,
                                             json.dumps(requests_data),
                                             headers=header,
                                             params=params).json()
                    _logger.debug('API Response: %s', response)

                    if 'detail' in response:
                        raise UserError(response['detail'])
                    if 'message' in response:
                        if response['message'] == 'Unauthenticated.' or response['message'] == '':
                            raise UserError(_("Authentication error with the API"))
                        else:
                            if 'errors' in response:
                                raise UserError(response['message'] + '/ errors: ' + str(response['errors']))
                            else:
                                raise UserError(response['message'])
                    elif 'is_valid' in response:
                        rec.write_response(response, payload)
                        if response['is_valid']:
                            # self.env.user.notify_success(message=_("The validation at DIAN has been successful."))
                            _logger.debug("The validation at DIAN has been successful.")
                        elif 'zip_key' in response or 'uuid' in response:
                            if response['zip_key'] is not None or response['uuid'] is not None:
                                if not rec.edi_is_not_test:
                                    # self.env.user.notify_success(message=_("Document sent to DIAN in testing."))
                                    _logger.debug("Document sent to DIAN in testing.")
                                else:
                                    temp_message = {rec.edi_status_message, rec.edi_errors_messages,
                                                    rec.edi_status_description, rec.edi_status_code}
                                    raise UserError(str(temp_message))
                            else:
                                raise UserError(_('A valid Zip key or UUID was not obtained. Try again.'))
                        else:
                            raise UserError(_('The document could not be validated in DIAN.'))
                    else:
                        raise UserError(_("No logical response was obtained from the API."))
                else:
                    raise UserError(_("A zip key or UUID is required to check the status of the document."))

            except Exception as e:
                _logger.debug("Failed to process the request: %s", e)
                raise UserError(_("Failed to process the request: %s") % e)

    def refund_sheet(self):
        self.ensure_one()
        res = super(HrPayslip, self).refund_sheet()

        for payslip in self:
            if payslip.credit_note:
                raise UserError(_("A adjustment note should not be made to a adjustment note"))

            # Only compatible with one record (one payslip), with ensure_one()
            copied_payslips_ids = res['domain'][0][2]
            copied_payslip = self.env['hr.payslip'].search([('id', 'in', copied_payslips_ids)])[0]

            copied_payslip.write({
                'origin_payslip_id': payslip.id,
                'number': _('New'),
            })

            if payslip.edi_payload and not copied_payslip.edi_payload:
                payload = copied_payslip.get_json_request()
                copied_payslip.write({'edi_payload': json.dumps(payload, indent=2, sort_keys=False)})

        return res

    # @api.depends('state')
    # def _compute_color(self):
    #     for rec in self:
    #         switcher = {
    #             'draft': 11,
    #             'verify': 2,
    #             'cancel': 1,
    #             'done': 0
    #         }
    #         rec.color = switcher.get(rec.state, 11)
