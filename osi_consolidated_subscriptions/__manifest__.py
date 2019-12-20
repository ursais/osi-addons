# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale Subscription Consolidated Subscription Invoices",
    "summary": "Consolidated subscription bill dates",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": [
        'sale_subscription',
        'account_invoice_consolidated'
    ],
    "data": [
        "data/consolidated_invoice_data.xml",
        "views/res_partner.xml",
        "wizard/change_bill_date_wizard.xml"
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["osi-scampbell"],
}
