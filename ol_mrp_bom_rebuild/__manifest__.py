{
    "name": "OnLogic MRP BOM Rebuild",
    "summary": "OnLogic MRP BOM Rebuild.",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "product_configurator_mrp",
        "ol_mrp_plm",
    ],
    # always loaded
    "data": [
        "data/product_data.xml",
        "views/mrp_bom_view.xml",
    ],
}
