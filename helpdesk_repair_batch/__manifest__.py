{
    "name": "Helpdesk - Repair Batches",
    "description": """
        Create Multiple Repair Orders from Tickets with batch actions.
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Helpdesk/Repairs",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "helpdesk_repair",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/helpdesk_ticket_views.xml",
        "views/repair_batch.xml",
        "views/repair_views.xml",
        "wizard/helpdesk_ticket_import_sale_views.xml",
    ],
    "installable": True,
}
