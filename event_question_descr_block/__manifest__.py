# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Event Questions - add description and can block registration',
    'category': 'Events',
    'summary': 'Event Questions - add description and can block registration',
    'version': '16.0.1.0.1',
    'description': """
Event Questions - add description and can block registration.
    """,
    'depends': ['website_event_questions'],
    'data': [
        "views/event_event_view_form.xml",
    ],
    'installable': True,
    'license': 'LGPL-3',
}
