# -*- coding: utf-8 -*-
# Copyright 2024 Open Source Integrators Inc
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Name Sequence Fix",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Fix duplicate journal entry names in concurrent posting scenarios",
    "description": """
        This module fixes the issue where interbank transfers and other processes
        that create multiple journal entries simultaneously cause duplicate name
        conflicts when using the OCA account_move_name_sequence module.
        
        The fix implements:
        - Thread-safe sequence generation with duplicate detection
        - Retry mechanism for handling concurrent sequence generation
        - Graceful error handling for concurrent posting scenarios
    """,
    "author": "Open Source Integrators Inc",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "account",
        "account_move_name_sequence",
    ],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
