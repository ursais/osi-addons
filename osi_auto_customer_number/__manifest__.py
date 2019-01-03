# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Auto Customer Integer Number",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "Generate Automatic customer integer number",
    "category": "Customers",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["base"],
    "data": [
        "data/ir_sequence_data.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
}
