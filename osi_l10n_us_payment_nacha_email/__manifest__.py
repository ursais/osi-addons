# Copyright (C) 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Batch Payment Nacha Email",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "depends": [
        "osi_ap_addresses",
        "l10n_us_payment_nacha",
    ],
    "data": [
        "data/mail_template_data.xml",
        "data/function.xml",
        "data/server_action_data.xml",
        "report/report_payment_receipt_templates.xml",
        "views/account_batch_payment_views.xml",
    ],
    "application": False,
    "maintainers": ["opensourceintegrators"],
}
