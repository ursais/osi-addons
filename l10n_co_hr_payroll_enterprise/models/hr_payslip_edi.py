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
import datetime as dt
import json
import logging
from copy import deepcopy

import babel
import requests
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrPayslipEdi(models.Model):
    _name = "hr.payslip.edi"
    _description = "Payslip Edi"

    note = fields.Text(string='Internal Note', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
                                  states={'draft': [('readonly', False)]})
    credit_note = fields.Boolean(string='Adjustment note', readonly=True, states={'draft': [('readonly', False)]},
                                 help="Indicates this edi payslip has a refund of another")
    origin_payslip_id = fields.Many2one(comodel_name="hr.payslip.edi", string="Origin Edi payslip", readonly=True,
                                        states={'draft': [('readonly', False)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    name = fields.Char(string='Edi Payslip Name', compute='_compute_name', store=True)

    # They allow storing synchronous and production modes used when invoicing
    edi_sync = fields.Boolean(string="Sync", default=False, copy=False)
    edi_is_not_test = fields.Boolean(string="In production", default=False, copy=False)

    # Edi fields
    date = fields.Date("Date", required=True, readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today, copy=False)
    payment_form_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.payment_forms", string="Payment form",
                                      default=1, readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    payment_method_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.payment_methods", string="Payment method",
                                        default=1, readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    accrued_total_amount = fields.Monetary("Accrued", currency_field='currency_id', readonly=True,
                                           states={'draft': [('readonly', False)]}, copy=True)
    deductions_total_amount = fields.Monetary("Deductions", currency_field='currency_id', readonly=True,
                                              states={'draft': [('readonly', False)]}, copy=True)
    total_amount = fields.Monetary("Total", currency_field='currency_id', readonly=True,
                                   states={'draft': [('readonly', False)]}, copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=False, compute='_compute_currency')
    worked_days_total = fields.Integer("Worked days", default=0)

    # Edi response fields
    edi_is_valid = fields.Boolean("Is valid?", copy=False)
    edi_is_restored = fields.Boolean("Is restored?", copy=False)
    edi_algorithm = fields.Char("Algorithm", copy=False)
    edi_class = fields.Char("Class", copy=False)
    edi_number = fields.Char("Number", copy=False)
    edi_uuid = fields.Char("UUID", copy=False)
    edi_issue_date = fields.Date("Date", copy=False)
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

    payslip_ids = fields.Many2many(comodel_name='hr.payslip', string='Payslips',
                                   relation='hr_payslip_hr_payslip_edi_rel',
                                   readonly=True, states={'draft': [('readonly', False)]}, copy=True)

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
    ], string='Month', index=True, copy=False, required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: str(fields.Date.context_today(self).month))
    year = fields.Integer(string='Year', index=True, copy=False, required=True, readonly=True,
                          states={'draft': [('readonly', False)]},
                          default=lambda self: fields.Date.context_today(self).year)

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
        for rec in self:
            if rec.edi_payload:
                try:
                    rec.edi_payload_html = rec.payload2html(json.loads(rec.edi_payload), 2)
                except json.decoder.JSONDecodeError as e:
                    rec.edi_payload_html = rec.payload2html(ast.literal_eval(rec.edi_payload), 2)
            else:
                rec.edi_payload_html = ""

    @api.depends('employee_id', 'month', 'year')
    def _compute_name(self):
        for rec in self:
            if (not rec.employee_id) or (not rec.month) or (not rec.year):
                return

            employee = self.employee_id

            date_ym = dt.date(rec.year, int(rec.month), 1)
            locale = self.env.context.get('lang') or 'en_US'
            rec.name = _('Salary Slip of %s for %s') % (
                employee.name,
                tools.ustr(babel.dates.format_date(date=date_ym, format='MMMM-y', locale=locale))
            )

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a Edi payslip which is not draft or cancelled!'))
        return super(HrPayslipEdi, self).unlink()

    def action_payslip_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
        return True

    def action_payslip_cancel(self):
        for rec in self:
            if not rec.edi_is_valid:
                rec.write({'state': 'cancel'})
            else:
                raise UserError(_("You cannot cancel a electronic payroll that has already been validated to the DIAN"))
        return True

    def _compute_currency(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id

    def compute_sheet(self):
        for rec in self:
            number = rec.number or _('New')

            # The date is the sending date
            date = fields.Date.context_today(self)

            # Save
            rec.write({
                'number': number,
                'date': date,
            })

            # Payload
            payload = rec.get_json_request()
            edi_payload = json.dumps(payload, indent=4, sort_keys=False)

            # Save
            rec.write({
                'edi_sync': rec.company_id.edi_payroll_is_not_test,
                'edi_is_not_test': rec.company_id.edi_payroll_is_not_test,
                'edi_payload': edi_payload,
            })

        return True

    @api.model
    def join_dicts(self, a, b, date_issue):
        if dt.datetime.strptime(a['period']['settlement_start_date'], '%Y-%m-%d') \
                < dt.datetime.strptime(b['period']['settlement_start_date'], '%Y-%m-%d'):
            first, last = deepcopy(a), deepcopy(b)
        else:
            first, last = deepcopy(b), deepcopy(a)

        # Root
        self.dict_root_sum(first, last, [
            'accrued_total',
            'deductions_total',
            'total'
        ])

        self.dict_root_append_lists(first, last, [
            'notes',
            'payment_dates'
        ])

        # Sequence
        if 'sequence' in last:
            last.pop('sequence')

        # Period
        self.dict_root_merge(first['period'], last['period'], [
            'admission_date',
            'settlement_start_date'
        ])
        last['period']['date_issue'] = date_issue

        # Earn
        self.dict_root_sum(first['earn'], last['earn'], [
            'endowment',
            'sustainment_support',
            'telecommuting',
            'company_withdrawal_bonus',
            'compensation',
            'refund'
        ])
        self.dict_sum_2(first, last, 'earn', 'basic', [
            'worked_days',
            'worker_salary'
        ])
        self.dict_sum_2(first, last, 'earn', 'primas', [
            'quantity',
            'payment',
            'non_salary_payment'
        ])
        self.dict_sum_2(first, last, 'earn', 'layoffs', [
            'payment',
            'interest_payment'
        ], ['percentage'])

        self.dict_root_append_dicts(first['earn'], last['earn'], [
            'vacation',
            'licensings'
        ])

        self.dict_root_append_lists(first['earn'], last['earn'], [
            'transports',
            'overtimes_surcharges',
            'incapacities',
            'bonuses',
            'assistances',
            'legal_strikes',
            'other_concepts',
            'compensations',
            'vouchers',
            'commissions',
            'third_party_payments',
            'advances'
        ])

        # Deduction
        self.dict_sum_1(first, last, 'deduction', [
            'voluntary_pension',
            'withholding_source',
            'afc',
            'cooperative',
            'tax_lien',
            'complementary_plans',
            'education',
            'refund',
            'debt'
        ])
        self.dict_sum_2(first, last, 'deduction', 'health', [
            'payment'
        ], ['percentage'])
        self.dict_sum_2(first, last, 'deduction', 'pension_fund', [
            'payment'
        ], ['percentage'])
        self.dict_sum_2(first, last, 'deduction', 'pension_security_fund', [
            'payment',
            'payment_subsistence'
        ], ['percentage', 'percentage_subsistence'])

        self.dict_append_lists_1(first, last, 'deduction', [
            'trade_unions',
            'sanctions',
            'libranzas',
            'third_party_payments',
            'advances',
            'other_deductions'
        ])

        return last

    def get_json_request(self):
        for rec in self:
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
            # if not rec.date_from:
            #     raise UserError(_("The payroll must have a period"))
            # if not rec.date_to:
            #     raise UserError(_("The payroll must have a period"))
            if not rec.payment_form_id:
                raise UserError(_("The payroll must have a payment form"))
            if not rec.payment_method_id:
                raise UserError(_("The payroll must have a payment method"))
            # if not rec.payment_date:
            #     raise UserError(_("The payroll must have a payment date"))
            if not rec.month:
                raise UserError(_("The payroll must have a month"))
            if not rec.year:
                raise UserError(_("The payroll must have a year"))

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

            json_request = {}

            # Others fields
            if rec.payslip_ids:
                for index, payslip in enumerate(rec.payslip_ids):
                    if index > 0:
                        json_request = rec.join_dicts(json_request, json.loads(payslip.edi_payload),
                                                      fields.Date.to_string(rec.date))
                    else:
                        json_request = json.loads(payslip.edi_payload)

            # Sequence
            if sequence:
                json_request['sequence'] = sequence

            # Notes
            if rec.note:
                notes = [{
                    "text": rec.note
                }]
                json_request['notes'] = notes

            # Save
            rec.write({
                'payment_form_id': json_request['payment']['code'],
                'payment_method_id': json_request['payment']['method_code'],
                'accrued_total_amount': json_request['accrued_total'],
                'deductions_total_amount': json_request['deductions_total'],
                'total_amount': json_request['total'],
                'worked_days_total': json_request['earn']['basic']['worked_days'],
            })

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
                if not rec.company_id.edi_payroll_enable or not rec.company_id.edi_payroll_consolidated_enable:
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
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip.edi.note')
                else:
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip.edi')

            if not self.env.context.get('without_compute_sheet'):
                rec.compute_sheet()
            rec.write({'state': 'done'})

            if rec.company_id.edi_payroll_enable and rec.company_id.edi_payroll_consolidated_enable:
                rec.validate_dian_generic()

        return True

    def status_zip(self):
        for rec in self:
            try:
                if not rec.company_id.edi_payroll_enable or not rec.company_id.edi_payroll_consolidated_enable:
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
        refund_payslip = None
        for payslip in self:
            if payslip.credit_note:
                raise UserError(_("A adjustment note should not be made to a adjustment note"))

            refund_payslip = payslip.copy({'credit_note': True,
                                           'name': _('Refund: ') + payslip.name,
                                           'origin_payslip_id': payslip.id,
                                           'number': _('New'),
                                           })
            refund_payslip.with_context(without_compute_sheet=True).action_payslip_done()

            if payslip.edi_payload and not refund_payslip.edi_payload:
                payload = refund_payslip.get_json_request()
                refund_payslip.write({'edi_payload': json.dumps(payload, indent=2, sort_keys=False)})

        formview_ref = self.env.ref('l10n_co_hr_payroll_enterprise.view_hr_payslip_edi_form', False)
        treeview_ref = self.env.ref('l10n_co_hr_payroll_enterprise.view_hr_payslip_edi_tree', False)

        if refund_payslip is not None:
            domain = "[('id', 'in', %s)]" % refund_payslip.ids
        else:
            domain = "[(credit_note, '=', True)]"

        return {
            'name': ("Refund Edi Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip.edi',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

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

    # Root
    @api.model
    def dict_root_sum(self, first, last, fields=[]):
        for field in fields:
            self.dict_root_sum_field(first, last, field)

    @api.model
    def dict_root_merge(self, first, last, fields=[]):
        for field in fields:
            self.dict_root_merge_field(first, last, field)

    @api.model
    def dict_root_sum_field(self, first, last, field):
        if field in first:
            if field not in last:
                last[field] = first[field]
            else:
                last[field] += first[field]

    @api.model
    def dict_root_merge_field(self, first, last, field):
        if field in first:
            last[field] = first[field]

    @api.model
    def dict_root_append_lists(self, first, last, list_fields):
        for list_field in list_fields:
            if list_field in first:
                if list_field not in last:
                    last[list_field] = []
                for temp_dict in first[list_field]:
                    last[list_field].append(temp_dict)

    @api.model
    def dict_root_append_dicts(self, first, last, dict_fields):
        for dict_field in dict_fields:
            if dict_field in first:
                if dict_field not in last:
                    last[dict_field] = {}
                self.dict_root_append_lists(first[dict_field], last[dict_field], first[dict_field])

    # Others
    @api.model
    def dict_append_lists_1(self, first, last, b, c=[]):
        if b in first:
            if b not in last:
                last[b] = {}
            self.dict_root_append_lists(first[b], last[b], c)

    @api.model
    def dict_sum_1(self, first, last, b, c=[], d=[]):
        if b in first:
            if b not in last:
                last[b] = {}
            self.dict_root_sum(first[b], last[b], c)
            self.dict_root_merge(first[b], last[b], d)

    @api.model
    def dict_sum_2(self, first, last, a, b, c=[], d=[]):
        if a in first:
            if a not in last:
                last[a] = {}
            if b in first[a]:
                if b not in last[a]:
                    last[a][b] = {}
                self.dict_root_sum(first[a][b], last[a][b], c)
                self.dict_root_merge(first[a][b], last[a][b], d)

    @api.model
    def dict_merge_field(self, first, last, a, b, c):
        if c in first[a][b]:
            if c not in last[a][b]:
                last[a][b][c] = first[a][b][c]

    @api.model
    def dict_sum_field(self, first, last, a, b, c):
        if c in first[a][b]:
            if c not in last[a][b]:
                last[a][b][c] = first[a][b][c]
            else:
                last[a][b][c] += first[a][b][c]

    @api.model
    def get_json2html_field_name(self, field_name, key):
        field_names = {
            "_sync": _("Sync"),
            "_rounding": _("Rounding"),
            "_accrued_total": _("Accrued total"),
            "_deductions_total": _("Deductions total"),
            "_total": _("Total"),
            "_environment": _("Environment"),
            "_environment_software": _("Software ID"),
            "_environment_pin": _("Software pin"),
            "_novelty": _("Novelty"),
            "uuid": _("UUID"),
            "_sequence": _("Sequence"),
            "worker_code": _("Worker code"),
            "prefix": _("Prefix"),
            "number": _("Number"),
            "_provider": _("Provider"),
            "name": _("Name"),
            "surname": _("Surname"),
            "second_surname": _("Second surname"),
            "first_name": _("First name"),
            "other_names": _("Other names"),
            "_information": _("Information"),
            "payroll_period_code": _("Payroll period"),
            "currency_code": _("Currency"),
            "trm": _("Trm"),
            "_employer": _("Employer"),
            "id_code": _("Document type"),
            "id_number": _("Document number"),
            "country_code": _("Country"),
            "municipality_code": _("Municipality"),
            "address": _("Address"),
            "_employee": _("Employee"),
            "type_worker_code": _("Worker type"),
            "subtype_worker_code": _("Worker subtype"),
            "high_risk_pension": _("High risk pension"),
            "integral_salary": _("Integral salary"),
            "contract_code": _("Contract type"),
            "salary": _("Salary"),
            "_period": _("Period"),
            "admission_date": _("Admission date"),
            "withdrawal_date": _("Withdrawal date"),
            "settlement_start_date": _("Settlement start date"),
            "settlement_end_date": _("Settlement end date"),
            "amount_time": _("Amount time"),
            "date_issue": _("Date issue"),
            "_payment": _("Payment"),
            "_payment_code": _("Payment form"),
            "_payment_method_code": _("Payment method"),
            "bank": _("Bank"),
            "account_type": _("Account type"),
            "account_number": _("Account number"),
            "_earn": _("Earn"),
            "endowment": _("Endowment"),
            "sustainment_support": _("Sustainment support"),
            "telecommuting": _("Telecommuting"),
            "company_withdrawal_bonus": _("Company withdrawal bonus"),
            "compensation": _("Compensation"),
            "refund": _("Refund"),
            "basic": _("Basic"),
            "worked_days": _("Worked days"),
            "worker_salary": _("Worked salary"),
            "vacation": _("Vacation"),
            "primas": _("Primas"),
            "layoffs": _("Layoffs"),
            "licensings": _("Licensings"),
            "transports": _("Transports"),
            "overtimes_surcharges": _("Overtimes and surcharges"),
            "incapacities": _("Incapacities"),
            "bonuses": _("Bonuses"),
            "assistances": _("Assistances"),
            "legal_strikes": _("Legal strikes"),
            "other_concepts": _("Other concepts"),
            "compensations": _("Compensations"),
            "vouchers": _("Vouchers"),
            "commissions": _("Commissions"),
            "third_party_payments": _("Third party payments"),
            "advances": _("Advances"),
            "_deduction": _("Deduction"),
            "_notes": _("Notes"),
            "_payment_dates": _("Payment dates"),
            "date": _("Date"),
            "start": _("Start"),
            "end": _("End"),
            "quantity": _("Quantity"),
            "payment": _("Payment"),
            "non_salary_payment": _("Non salary payment"),
            "percentage": _("Percentage"),
            "interest_payment": _("Interest payment"),
            "assistance": _("Assistance"),
            "viatic": _("Viatic"),
            "non_salary_viatic": _("Non salary viatic"),
            "time_code": _("Overtime and surcharges type"),
            "incapacity_code": _("Incapacity type"),
            "description": _("Description"),
            "ordinary": _("Ordinary"),
            "extraordinary": _("Extraordinary"),
            "salary_food_payment": _("Salary food payment"),
            "non_salary_food_payment": _("Non salary food payment"),
            "voluntary_pension": _("Voluntary pension"),
            "withholding_source": _("Withholding source"),
            "afc": _("Afc"),
            "cooperative": _("Cooperative"),
            "tax_lien": _("Tax lien"),
            "complementary_plans": _("Complementary plans"),
            "education": _("Education"),
            "debt": _("Debt"),
            "percentage_subsistence": _("Percentage subsistence"),
            "payment_subsistence": _("Payment subsistence"),
            "payment_public": _("Payment public"),
            "payment_private": _("Payment private"),
            "text": _("Text"),
            "other_deductions": _("Other deductions"),
            "libranzas": _("Libranzas"),
            "sanctions": _("Sanctions"),
            "trade_unions": _("Trade unions"),
            "_deduction_pension_security_fund": _("Pension security fund"),
            "_deduction_pension_fund": _("Pension fund"),
            "health": _("Health"),
            "_earn_vacation_common": _("Vacation common"),
            "_earn_vacation_compensated": _("Vacation compensated"),
            "_earn_licensings_licensings_maternity_or_paternity_leaves": _("Maternity or paternity leaves"),
            "_earn_licensings_licensings_permit_or_paid_licenses": _("Permit or paid licenses"),
            "_earn_licensings_licensings_suspension_or_unpaid_leaves": _("Suspension or unpaid leaves"),
            "_payroll_reference": _("Reference"),
            "issue_date": _("Issue date"),
        }

        if field_name in field_names:
            return field_names[field_name]
        elif key in field_names:
            return field_names[key]
        else:
            return field_name

    @api.model
    def payload2html(self, payload, tab, title=""):
        output = ""
        output_temp = "<table class='o_group o_inner_group o_group_col_12'><tbody>"
        for key, value in payload.items():
            field_name = title + "_" + key
            if type(value) != dict and type(value) != list:
                if key == 'sync':
                    continue
                if key[-4:] == 'code':
                    model_names = {
                        "payroll_period_code": "l10n_co_edi_jorels.payroll_periods",
                        "currency_code": "l10n_co_edi_jorels.type_currencies",
                        "id_code": "l10n_co_edi_jorels.type_document_identifications",
                        "municipality_code": "l10n_co_edi_jorels.municipalities",
                        "type_worker_code": "l10n_co_edi_jorels.type_workers",
                        "subtype_worker_code": "l10n_co_edi_jorels.subtype_workers",
                        "country_code": "l10n_co_edi_jorels.countries",
                        "contract_code": "l10n_co_edi_jorels.type_contracts",
                        "_payment_code": "l10n_co_edi_jorels.payment_forms",
                        "_payment_method_code": "l10n_co_edi_jorels.payment_methods",
                        "time_code": "l10n_co_edi_jorels.type_times",
                        "incapacity_code": "l10n_co_edi_jorels.type_incapacities",
                    }
                    try:
                        if field_name in model_names:
                            value = self.env[model_names[field_name]].search([('id', '=', value)])[0].name
                        elif key in model_names:
                            value = self.env[model_names[key]].search([('id', '=', value)])[0].name
                    except IndexError as e:
                        pass
                output_temp += "<tr><td class='o_td_label' style='width: 50%;'><label class='o_form_label'><strong>" + \
                               self.get_json2html_field_name(field_name, key) + \
                               "</strong></label></td>" \
                               "<td class='text-right' style='width: 100%;'><span class='o_field_char o_field_widget'>" + \
                               str(value) + \
                               "</span></td><td/></tr>"
        if output_temp != "<table class='o_group o_inner_group o_group_col_12'><tbody>":
            output_temp += "</tbody></table><br/><br/>"
            output += output_temp

        for key, value in payload.items():
            field_name = title + "_" + key
            if type(value) == dict:
                if key == 'environment':
                    continue
                output += "<h" + str(tab) + ">" + \
                          self.get_json2html_field_name(field_name, key) + "</h" + str(tab) + ">"
                output += self.payload2html(value, tab + 1, field_name)

        for key, value in payload.items():
            field_name = title + "_" + key
            if type(value) == list:
                output += "<h" + str(tab) + ">" + \
                          self.get_json2html_field_name(field_name, key) + "</h" + str(tab) + ">"
                for i, valor in enumerate(value):
                    output += "<h" + str(tab + 1) + ">" + str(i + 1) + ". " + "</h" + str(tab + 1) + ">"
                    output += self.payload2html(valor, tab + 1, field_name)
        return output
