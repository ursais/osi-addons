{
    "name": "OnLogic MRP Customization",
    "summary": "Adds OnLogic MRP Customization",
    "description": """Adds OnLogic MRP Customization""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "mrp",
        "mrp_batch",
        "product_configurator_mrp_component"
    ],
    # always loaded
    "data": [
        "reports/mo_bin_label.xml",
        "views/mrp_production_view.xml",
        "views/product_template_view.xml",
        "views/stock_lot_view.xml",
    ],
}
