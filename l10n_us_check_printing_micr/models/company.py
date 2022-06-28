# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    # here, key has to be full xmlID(including the module name) of all the
    # new report actions that you have defined for check layout
    account_check_printing_layout = fields.Selection(
        selection_add=[
            (
                "l10n_us_check_printing_micr.action_print_check_top_micr",
                "Print Check (Top) - US MICR",
            ),
            (
                "l10n_us_check_printing_micr.action_print_check_middle_micr",
                "Print Check (Middle) - US MICR",
            ),
            (
                "l10n_us_check_printing_micr.action_print_check_bottom_micr",
                "Print Check (Bottom) - US MICR",
            ),
        ],
        ondelete={
            "l10n_us_check_printing_micr.action_print_check_top_micr": "set default",
            "l10n_us_check_printing_micr.action_print_check_middle_micr": "set default",
            "l10n_us_check_printing_micr.action_print_check_bottom_micr": "set default",
        },
    )
