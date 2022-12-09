# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI - Stock Cycle Count",
    "version": "15.0.1.0.0",
    "category": "Hidden",
    "license": "AGPL-3",
    "maintainers": "Open Source Integrators",
    "depends": ["stock_cycle_count"],
    "summary": """
     Adds functionality to send notification emails to cycle count followers before x days of inventory adjustment scheduled date.""",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "data": [
        "data/mail_templates.xml",
        "data/ir_cron_notify_users.xml",
        "views/stock_cycle_count_rule_view.xml",
        "views/stock_inventory_view.xml"
    ],
    "installable": True,
    "application": False,
}
