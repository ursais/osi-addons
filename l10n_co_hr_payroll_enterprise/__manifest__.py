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


{
    'name': 'Nómina electrónica DIAN para Colombia por Jorels SAS (Enterprise)',
    'summary': 'Nómina electrónica DIAN para Colombia por Jorels SAS (Enterprise)',
    'description': "Electronic payroll management for companies in Colombia (Enterprise)",
    'author': 'Jorels SAS',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'version': '16.0.23.06.15.17.58',
    'website': "https://www.jorels.com",
    'images': ['static/images/main_screenshot.png'],
    'support': 'info@jorels.com',
    'depends': [
        'hr_payroll',
        'l10n_co_edi_jorels',
    ],
    'data': [
        'data/hr_payroll_sequence.xml',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_payslip_edi_views.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
        'report/hr_payslip_edi_report.xml',
    ],
    'installable': True,
    'application': False,
}
