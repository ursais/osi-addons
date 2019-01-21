# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Field Service - Google Maps',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'summary': 'Auto-complete addresses with Google Maps',
    'author': 'Open Source Integrators',
    'maintainer': 'Open Source Integrators',
    'website': 'https://www.opensourceintegrators.com',
    'depends': [
        'web_google_maps',
        'fieldservice',
    ],
    'data': [
        'views/fsm_location.xml',
        'views/fsm_order.xml',
        'views/res_partner.xml',
    ],
    'development_status': 'Beta',
    'maintainers': [
        'osimallen',
    ],
}
