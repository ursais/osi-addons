# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Commissions Report",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Accounting/Reporting",
    "depends": ["account", "partner_commission"],
    "data": [
        "security/ir.model.access.csv",
        "views/commissions_report_views.xml",
    ],
    "application": False,
    "installable": True,
}
