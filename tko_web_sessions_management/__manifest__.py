# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
# Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
# Copyright (C) Open Source Integrators <http://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Web Sessions Management',
    'summary': '''Sessions timeout and forced termination.
        Multisession control. Login by calendar (week day hours).
        Remote IP filter and location.''',
    'author': 'TKO, OSI',
    'category': 'Extra Tools',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-br.com, http://www.opensourceintegrators.com',
    'version': '17.0.1.0.0',
    'depends': [
        'resource',
    ],
    'images': ['static/description/sessions_groups.png',
               'static/description/sessions_management.png',
               'static/description/sessions_pivot.png',
               'static/description/sessions_user_preferences.png',
               'static/description/sessions_users.png',],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduler.xml',
        'views/res_users_view.xml',
        'views/res_groups_view.xml',
        'views/ir_sessions_view.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tko_web_sessions_management/static/src/js/customize_session.js',
        ],
    },
    'installable': True,
}
