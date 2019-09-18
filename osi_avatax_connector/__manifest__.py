# Copyright (C) 2019 Odoo
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Avalara Avatax Connector",
    "version": "12.0.1.0.0",
    "author": "Fabrice Henrion, Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons/",
    "summary": "Tax Calculation using Avalara Avatax Services",
    "license": "LGPL-3",
    "category": "Accounting",
    "depends": [
        'account',
        'sale',
        'stock',
        'base_geolocalize',
    ],
    "data": [
        "security/avalara_salestax_security.xml",
        "security/ir.model.access.csv",
        "wizard/avalara_salestax_ping_view.xml",
        "wizard/avalara_salestax_address_validate_view.xml",
        "views/avalara_salestax_view.xml",
        "views/avalara_salestax_data.xml",
        "views/partner_view.xml",
        "views/product_view.xml",
        "views/account_invoice_action.xml",
        "views/account_invoice_view.xml",
        "views/sale_order_view.xml",
        "views/sale_order_action.xml",
        "views/account_tax_view.xml",
        "report/sale_order_templates.xml",
        # "views/res_config_settings_view.xml",
    ],
    'images': [
        'static/description/avatax.png',
    ],
    'installable': True,
    'application': True,
}
