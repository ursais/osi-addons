{
    "name": "Onlogic Helpdesk - Repair Batches",
    "description": """
        Create Multiple Repair Orders from Tickets with batch actions.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Helpdesk/Repairs",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "helpdesk_repair",
    ],
    # always loaded
    "data": [
        "data/ir_sequence.xml",
        "security/ir.model.access.csv",
        "views/helpdesk_team_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/repair_batch.xml",
        "views/repair_views.xml",
        "wizard/helpdesk_ticket_import_sale_views.xml",
    ],
    "installable": True,
}
