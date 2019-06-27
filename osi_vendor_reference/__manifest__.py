# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'OSI Vendor Reference',
    'version': '12.0.1.0.0',
    'author': 'Open Source Integrators',
    'summary': 
            '''
             When vendor bill is created, copy the vendor reference info from the PO into the bill.
             If the bill already has a reference, append to existing reference using ; [Bill can be for multiple PO's]
            ''',
    'category': 'Customers',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'depends': ['purchase', 'account'],
    'data': [ 
    ],
    'qweb': [        
    ],
    'installable': True,
}
