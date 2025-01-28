# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sequence_number_margin_top = fields.Float(
        related="company_id.sequence_number_margin_top",
        string="Sequence Number: Top",
        readonly=False,
        help="Adjust the margins of the sequence number on checks to make it fit your "
        "printer's settings.",
    )
    sequence_number_margin_left = fields.Float(
        related="company_id.sequence_number_margin_left",
        string="Sequence Number: Left",
        readonly=False,
        help="Adjust the margins of the sequence number on checks to make it fit your "
        "printer's settings.",
    )
    ckus_date_margin_top = fields.Float(
        related="company_id.ckus_date_margin_top",
        string="Date: Top",
        readonly=False,
        help="Adjust the margins of date on checks to make it fit your "
        "printer's settings.",
    )
    ckus_date_margin_left = fields.Float(
        related="company_id.ckus_date_margin_left",
        string="Date: Left",
        readonly=False,
        help="Adjust the margins of date on checks to make it fit your "
        "printer's settings.",
    )
    ckus_payee_name_margin_top = fields.Float(
        related="company_id.ckus_payee_name_margin_top",
        string="Payee Name: Top",
        readonly=False,
        help="Adjust the margins of the payee name on checks to make it fit your "
        "printer's settings.",
    )
    ckus_payee_name_margin_left = fields.Float(
        related="company_id.ckus_payee_name_margin_left",
        string="Payee Name: Left",
        readonly=False,
        help="Adjust the margins of the payee name on checks to make it fit your "
        "printer's settings.",
    )
    payee_address_margin_top = fields.Float(
        related="company_id.payee_address_margin_top",
        string="Payee Address: Top",
        readonly=False,
        help="Adjust the margins of the payee address on checks to make it fit your "
        "printer's settings.",
    )
    payee_address_margin_left = fields.Float(
        related="company_id.payee_address_margin_left",
        string="Payee Address: Left",
        readonly=False,
        help="Adjust the margins of the payee address on checks to make it fit your "
        "printer's settings.",
    )
    amount_margin_top = fields.Float(
        related="company_id.amount_margin_top",
        string="Amount: Top",
        readonly=False,
        help="Adjust the margins of the amount on checks to make it fit your "
        "printer's settings.",
    )
    amount_margin_left = fields.Float(
        related="company_id.amount_margin_left",
        string="Amount: Left",
        readonly=False,
        help="Adjust the margins of the amount on checks to make it fit your "
        "printer's settings.",
    )
    amount_word_margin_top = fields.Float(
        related="company_id.amount_word_margin_top",
        string="Amount Words: Top",
        readonly=False,
        help="Adjust the margins of the amount in words on checks to make it fit your "
        "printer's settings.",
    )
    amount_word_margin_left = fields.Float(
        related="company_id.amount_word_margin_left",
        string="Amount Words: Left",
        readonly=False,
        help="Adjust the margins of the amount in words on checks to make it fit your "
        "printer's settings.",
    )
    memo_margin_top = fields.Float(
        related="company_id.memo_margin_top",
        string="Memo: Top",
        readonly=False,
        help="Adjust the margins of the memo on checks to make it fit your "
        "printer's settings.",
    )
    memo_margin_left = fields.Float(
        related="company_id.memo_margin_left",
        string="Memo: Left",
        readonly=False,
        help="Adjust the margins of the memo on checks to make it fit your "
        "printer's settings.",
    )

    # TODO Onchange to auto set values when check layout changes
    # Further work needed, the below partially works but doesn't keep values on save
    # @api.onchange("account_check_printing_layout")
    # def account_check_printing_layout_onchange(self):
    #     if (
    #         self.account_check_printing_layout
    #         == "l10n_us_check_printing.action_print_check_top"
    #     ):
    #         self.sequence_number_margin_top = 0.1
    #         self.sequence_number_margin_left = 7.1
    #         self.ckus_date_margin_top = 0.55
    #         self.ckus_date_margin_left = 6.51
    #         self.ckus_payee_name_margin_top = 1.09
    #         self.ckus_payee_name_margin_left = 0.85
    #         self.payee_address_margin_top = 1.65
    #         self.payee_address_margin_left = 0.85
    #         self.amount_margin_top = 1.07
    #         self.amount_margin_left = 6.77
    #         self.amount_word_margin_top = 1.45
    #         self.amount_word_margin_left = 0.25
    #         self.memo_margin_top = 2.41
    #         self.memo_margin_left = 0.6
    #     elif (
    #         self.account_check_printing_layout
    #         == "l10n_us_check_printing.action_print_check_middle"
    #     ):
    #         self.sequence_number_margin_top = 0.0
    #         self.sequence_number_margin_left = 7.19
    #         self.ckus_date_margin_top = 0.1
    #         self.ckus_date_margin_left = 6.75
    #         self.ckus_payee_name_margin_top = 0.6
    #         self.ckus_payee_name_margin_left = 0.63
    #         self.payee_address_margin_top = 1.15
    #         self.payee_address_margin_left = 0.63
    #         self.amount_margin_top = 0.6
    #         self.amount_margin_left = 6.38
    #         self.amount_word_margin_top = 1.0
    #         self.amount_word_margin_left = 0.05
    #         self.memo_margin_top = 1.98
    #         self.memo_margin_left = 0.43
    #     elif (
    #         self.account_check_printing_layout
    #         == "l10n_us_check_printing.action_print_check_bottom"
    #     ):
    #         self.sequence_number_margin_top = 0.2
    #         self.sequence_number_margin_left = 6.51
    #         self.ckus_date_margin_top = 0.6
    #         self.ckus_date_margin_left = 6.51
    #         self.ckus_payee_name_margin_top = 1.08
    #         self.ckus_payee_name_margin_left = 0.9
    #         self.payee_address_margin_top = 1.65
    #         self.payee_address_margin_left = 1.0
    #         self.amount_margin_top = 1.08
    #         self.amount_margin_left = 6.77
    #         self.amount_word_margin_top = 1.47
    #         self.amount_word_margin_left = 0.25
    #         self.memo_margin_top = 2.45
    #         self.memo_margin_left = 0.6
    #     else:
    #         self.sequence_number_margin_top = 0.0
    #         self.sequence_number_margin_left = 0.0
    #         self.ckus_date_margin_top = 0.0
    #         self.ckus_date_margin_left = 0.0
    #         self.ckus_payee_name_margin_top = 0.0
    #         self.ckus_payee_name_margin_left = 0.0
    #         self.payee_address_margin_top = 0.0
    #         self.payee_address_margin_left = 0.0
    #         self.amount_margin_top = 0.0
    #         self.amount_margin_left = 0.0
    #         self.amount_word_margin_top = 0.0
    #         self.amount_word_margin_left = 0.0
    #         self.memo_margin_top = 0.0
    #         self.memo_margin_left = 0.0
