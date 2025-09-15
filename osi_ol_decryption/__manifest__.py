# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "OSI Decryption",
    'summary': """This module will decrypt the Char and Numeric type fields data""",
    'category': 'Base',
    'version': '17.0.1.0.0',
    "data": [
	    # "data/stock.location.csv",
	   ],
    'depends': ['base', 'stock'],
    'post_init_hook' : 'post_init_hook_encrypt_decrypt'
}
