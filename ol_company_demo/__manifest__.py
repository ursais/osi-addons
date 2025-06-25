# -*- coding: utf-8 -*-
{
    "name": "ol_company_demo",
    "summary": "Demo Module for Company Rules and Contexts",
    "description": """
This module is a demo module, intended to show how to properly handle company rules and contexts in Odoo.
    """,
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": ["base"],
    # Data Loaded.
    "data": [
        "security/security.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/products.xml",
    ],
}
