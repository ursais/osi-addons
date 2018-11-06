# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "OSI FSM Timeline Person Filter",
    'summary': "Enhancing web time line module to add advance person filters",
    "version": "11.0.0.0.0",
    "license": "AGPL-3",
    'author': 'Open Source Integrators,',
    "category": "web",
    "website": 'http://www.ursainfosystems.com',
    'depends': ["fieldservice", "web_timeline"],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'data': [
        'views/template.xml',
    ],
}
