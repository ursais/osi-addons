# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Multiple Salespersons",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Multiple Salespersons",
    "author": "Open Source Integrators",
    "maintainers": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": ["sale_stock", "osi_analytic_segments", "web_many2many_groupby"],
    "data": [
        "views/sale_order_view.xml",
        "views/res_partner_view.xml",
        "views/account_move_view.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
}
