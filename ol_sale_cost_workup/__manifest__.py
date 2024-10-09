{
    "name": "OnLogic Sale Cost Workup Report",
    "summary": "This module handles the Sale Cost Workup",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_sale",
        "ol_sale_optional_product",
    ],
    # always loaded
    "data": [
        "data/ir_actions_server.xml",
        "report/cost_workup_document.xml",
    ],
}
