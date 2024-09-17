{
    "name": "OnLogic MRP BOM Rebuild",
    "summary": "Rebuild Variant BoM's from scaffolding.",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_mrp_plm",
        "product_configurator_mrp_quantity",
    ],
    # always loaded
    "data": [
        "data/ir_actions_server.xml",
    ],
}
