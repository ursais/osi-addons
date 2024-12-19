# -*- coding: utf-8 -*-
{
    "name": "autologin",
    "summary": "Access odoo without password",
    "description": """
Automatically log in as administrator
=====================================

This module automatically authenticates somebody accessing the
login page as admin.

**Security warning** Use this module only on a demo environment
that needs open public access. Don't even think of deploying this
module on an actual production environment.
        """,
    "author": "frePPLe",
    "license": "Other OSI approved licence",
    "category": "Uncategorized",
    "version": "16.0.0",
    "depends": ["base", "web"],
    "data": [],
    "demo": [],
    "autoinstall": False,
    "installable": True,
    "price": 0,
    "currency": "EUR",
    "images": ["static/description/images/autologin.png"],
}
