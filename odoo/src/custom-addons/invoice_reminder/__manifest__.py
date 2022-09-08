# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Invoice Reminder Customization',
    'category': 'Tools',
    'summary': 'Invoice Reminder Customization',
    'description': """
    'author': 'Craig Kolobow',
    'maintainer': ['ckolobow'],
This module gives you a quick view of your contacts directory, accessible from your home page.
You can track your vendors, customers and other contacts.
""",
    'depends': ['base', 'mail', 'account_reports_followup'],
    'data': ['views/followup.xml'],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
