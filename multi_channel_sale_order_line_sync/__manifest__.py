# Copyright (C) 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Multi-Channel Sale Order Line Sync",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": """Append new channel line items (e.g. post-purchase upsell apps)
    to already-confirmed Sales Orders during multi-channel order
    import/update, instead of silently skipping them.""",
    "author": "Open Source Integrators",
    "maintainers": ["opensourceintegrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "odoo_multi_channel_sale",
    ],
    "data": [
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
