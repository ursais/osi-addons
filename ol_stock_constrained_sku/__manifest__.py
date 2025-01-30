{
    "name": "OnLogic Stock - Constrained SKU",
    "summary": "Allows user to Allocate / Un-Allocate SKUs in bulk",
    "version": "17.0.1.0.0",
    "depends": [
        "ol_base",
        # 'ls_sale',
        # 'ls_stock',
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Inventory",
    "description": "Allows user to Allocate / Un-Allocate SKUs in bulk",
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/constrained_sku_search_wizard.xml",
        "wizard/constrained_sku_wizard.xml",
        "wizard/constrained_sku_result_wizard.xml",
    ],
}
