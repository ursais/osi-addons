# Copyright 2016 Serpent Consulting Services Pvt. Ltd. (support@serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "OSI Ap Addresses",
    "summary": """OSI AP Addresses.""",
    "category": "Accounting",
    "version": "17.0.1.0.0",
    "author": "Open Source Integrators",
    "license": "AGPL-3",
    "depends": ["account", "account_check_printing", "l10n_us_check_printing", "contacts", "mail"],
    "data": [
        "data/mail_template_data.xml",
        "data/server_action_data.xml",
        "views/res_partner_views.xml",
        "views/account_payment_view.xml",
    ],
    "demo": [],
    "installable": True,
}
