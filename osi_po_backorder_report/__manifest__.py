# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI PO Backorder Report",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "Adds the ability to view and print a report of UIGR and "
               "Backorder quantities and values",
    "category": "Customers",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["purchase"],
    "data": [
        "views/po_backorder_view.xml",
        "views/purchase_view.xml",
        "report/po_backorder_report.xml",
        "wizard/po_backorder_wizard_view.xml",
    ],
    "installable": True,
}
