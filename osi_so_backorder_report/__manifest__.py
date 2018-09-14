# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI SO Backorder Report",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "Adds the ability to view and print a report of UIGD and "
               "Backorder quantities and values",
    "category": "Customers",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["sale", "sale_stock"],
    "data": [
        "views/so_backorder_view.xml",
        "views/sale_view.xml",
        "report/so_backorder_report.xml",
        "wizard/so_backorder_wizard_view.xml",
    ],
    "installable": True,
}
