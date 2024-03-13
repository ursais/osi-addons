# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from odoo import api, SUPERUSER_ID

from . import models
from . import wizard

# def post_init_hook(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})

#     env['ir.actions.server'].encrypt_char_fields()
#     env['ir.actions.server'].encrypting_numeric_fields()
