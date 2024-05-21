# -*- coding: utf-8 -*-
{
'name': 'Login as another user',
'summary': 'Login as/impersonate another user, Login As, Other Users, Admin Users, '
           'Administrator, Super User, Portal User, Portal Hijack',
'version': '17.0.1.2.3',
'category': 'Extra Tools',
'website': 'https://www.open-inside.com',
'description': '''
'''
               '''		 * allow administrator to login as/impersonate normal user
'''
               '''		 * allow administrator to login as/impersonate portal user
'''
               '''		 * login back to administrator
'''
               '''		 
'''
               '    ',
'images': ['static/description/cover.png'],
'author': 'Openinside',
'license': 'OPL-1',
'price': 30.0,
'currency': 'USD',
'installable': True,
'depends': ['web', 'portal'],
'data': ['view/login_as.xml',
         'view/templates.xml',
          'security/ir.model.access.csv',
          'view/action.xml'],
'external_dependencies': {},
'auto_install': True,
'odoo-apps': True,
'assets': {
        'web.assets_backend': ['oi_login_as/static/src/login_as/*.js',
                               'oi_login_as/static/src/login_as/*.xml',
                               ]
        },
'application': False
}