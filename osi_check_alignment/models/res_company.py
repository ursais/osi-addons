# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sequence_number_margin_top = fields.Float(
        string="Sequence Number: Top",
        default=0.0,
        help="Adjust the margins of the sequence number on checks to make it fit your "
        "printer's settings.",
    )
    sequence_number_margin_left = fields.Float(
        string="Sequence Number: Left",
        default=7.19,
        help="Adjust the margins of the sequence number on checks to make it fit your "
        "printer's settings.",
    )
    ckus_date_margin_top = fields.Float(
        string="Date: Top",
        default=0.55,
        help="Adjust the margins of date on checks to make it fit your "
        "printer's settings.",
    )
    ckus_date_margin_left = fields.Float(
        string="Date: Left",
        default=6.51,
        help="Adjust the margins of date on checks to make it fit your "
        "printer's settings.",
    )
    ckus_payee_name_margin_top = fields.Float(
        string="Payee Name: Top",
        default=1.09,
        help="Adjust the margins of the payee name on checks to make it fit your "
        "printer's settings.",
    )
    ckus_payee_name_margin_left = fields.Float(
        string="Payee Name: Left",
        default=0.85,
        help="Adjust the margins of the payee name on checks to make it fit your "
        "printer's settings.",
    )
    payee_address_margin_top = fields.Float(
        string="Payee Address: Top",
        default=1.65,
        help="Adjust the margins of the payee address on checks to make it fit your "
        "printer's settings.",
    )
    payee_address_margin_left = fields.Float(
        string="Payee Address: Left",
        default=0.85,
        help="Adjust the margins of the payee address on checks to make it fit your "
        "printer's settings.",
    )
    amount_margin_top = fields.Float(
        string="Amount: Top",
        default=1.07,
        help="Adjust the margins of the amount on checks to make it fit your "
        "printer's settings.",
    )
    amount_margin_left = fields.Float(
        string="Amount: Left",
        default=6.77,
        help="Adjust the margins of the amount on checks to make it fit your "
        "printer's settings.",
    )
    amount_word_margin_top = fields.Float(
        string="Amount Words: Top",
        default=1.45,
        help="Adjust the margins of the amount in words on checks to make it fit your "
        "printer's settings.",
    )
    amount_word_margin_left = fields.Float(
        string="Amount Words: Left",
        default=0.25,
        help="Adjust the margins of the amount in words on checks to make it fit your "
        "printer's settings.",
    )
    memo_margin_top = fields.Float(
        string="Memo: Top",
        default=2.41,
        help="Adjust the margins of the memo on checks to make it fit your "
        "printer's settings.",
    )
    memo_margin_left = fields.Float(
        string="Memo: Left",
        default=0.6,
        help="Adjust the margins of the memo on checks to make it fit your "
        "printer's settings.",
    )
