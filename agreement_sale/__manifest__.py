# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale - Agreement",
    "summary": "Link a helpdesk ticket to an agreement",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "category": "Helpdesk",
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "sale",
        "agreement",
    ],
    "data": [
        "views/agreement.xml",
        "views/sale_order.xml"
    ],
    "installable": True,
}
