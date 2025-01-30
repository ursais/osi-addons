{
    "name": "OnLogic Stock - Constrained SKU",
    "summary": "Allows user to Allocate / Un-Allocate SKUs in bulk",
    "description": "Allows user to Allocate / Un-Allocate SKUs in bulk",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Inventory",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "stock",
    ],
    # always loaded
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/constrained_sku_search_wizard.xml",
        "wizard/constrained_sku_wizard.xml",
        "wizard/constrained_sku_result_wizard.xml",
    ],
}
