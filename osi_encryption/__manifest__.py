# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "OSI Encryption and Sanitization",
    "summary": """This module will allow users to encrypt/sanitize data""",
    "category": "Base",
    "version": "14.0.1.0.0",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/server_action.xml",
        "wizard/decrypt_wizard.xml",
        "wizard/encrypt_wizard.xml",
        "wizard/drop_index_wizard.xml",
        "wizard/generate_lines_wizard_view.xml",
        "views/encrypt_views.xml",
    ],
    # 'post_init_hook' : 'post_init_hook'
}
