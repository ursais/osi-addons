# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Voicent Helpdesk Ticket Connector",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "category": "connector",
    "author": "Open Source Integrators, "
              "Odoo Community Association (OCA)",
    "summary": """This module aims to automate calls to customer
    or impacted third parties when a ticket reaches a specific stage.""",
    "website": "https://github.com/OCA/connector-telephony",
    "depends": [
        "connector_voicent",
        "helpdesk"
    ],
    'maintainers': [
        'max3903',
    ],
    "data": ['view/queue_job_view.xml',
             'view/backend_voicent_call_line_view.xml',
             ],
    "installable": True,
}
