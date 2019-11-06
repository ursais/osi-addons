# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk - Field Service',
    'summary': 'Create service requests from a ticket',
    'version': '12.0.1.1.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Helpdesk',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk_timesheet',
        'fieldservice',
    ],
    'data': [
        'views/helpdesk_ticket_views.xml',
        'views/fsm_location_views.xml',
        'views/fsm_order_views.xml',
        'views/res_partner.xml'
    ],
    'installable': True,
}
