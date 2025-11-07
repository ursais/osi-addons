# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Gmail Fix",
    "summary": "Fix missing google_gmail_client_identifier field in res.config.settings",
    "description": """
        This module adds the missing google_gmail_client_identifier field to
        res.config.settings model. This field is required by Gmail integration
        modules but was missing from the database schema, causing errors when
        accessing email server settings under Discuss > General Settings.
    """,
    "version": "12.0.1.0.0",
    "category": "Mail",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "license": "AGPL-3",
    "depends": ["base", "mail"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
