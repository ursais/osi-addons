# Copyright (C) 2023 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Mexican Addendum For Invoices For Ford",
    "version": "17.0.1.1.0",
    "license": "LGPL-3",
    "summary": "Mexican Localization Addendum For Ford",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "account",
        "l10n_mx_edi",
    ],
    "data": ["views/account_move_views.xml", "views/l10n_mx_addenda_ford_view.xml"],
    "application": False,
    "maintainers": ["ursais"],
}
