# Copyright (C) 2024, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    nacha_file_type = fields.Selection(
        [("80_byte", "80 Byte")],
        default="80_byte",
        string="File Type",
    )
