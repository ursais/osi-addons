# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk - Field Service - Agreement',
    'summary': 'Carry over agreement values when creating service requests',
    'version': '11.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Helpdesk',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'agreement_helpdesk',
        'helpdesk_fieldservice',
    ],
    'data': [
        'views/helpdesk_ticket_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
