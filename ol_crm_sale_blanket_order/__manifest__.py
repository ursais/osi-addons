{
    "name": "Onlogic CRM Sale Blanket Order",
    "summary": """
        Adds the ability to create Blanket Orders from CRM Opportunities.
        """,
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "CRM",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "sale_blanket_order",
        "crm",
    ],
    # Data Loaded.
    "data": [
        "views/crm_lead_views.xml",
        "views/blanket_order_view.xml",
    ],
}
