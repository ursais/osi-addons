# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "US Check Printing with MICR Font",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "US Check Printing With MICR Font",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": ["l10n_us_check_printing"],
    "data": [
        "data/us_check_printing.xml",
        "report/print_check.xml",
        "report/print_check_top.xml",
        "report/print_check_middle.xml",
        "report/print_check_bottom.xml",
        "views/res_partner_bank.xml",
    ],
    "installable": True,
    "maintainers": "[opensourceintegrators]",
}
