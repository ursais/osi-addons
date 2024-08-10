{
    "name": "OnLogic MRP BOM Rebuild",
    "summary": "OnLogic MRP BOM Rebuild.",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product_configurator_mrp",
        "ol_mrp_plm",
    ],
    # always loaded
    "data": [
        "data/ir_actions_server.xml",
    ],
}
