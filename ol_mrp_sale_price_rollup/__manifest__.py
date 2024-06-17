# pylint: disable=pointless-statement
{
    "name": "OnLogic MRP Sale Price Rollup",
    "summary": "OnLogic MRP Sale Price Rollup Customization.",
    "description": """
        A Sales Price Roll-up from the Components of a Sellable Product
        which is manufactured from Components in various BOM Levels
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": ["sale", "mrp", "mrp_account", "product_configurator"],
    # always loaded
    "data": [
        "views/product_view.xml",
        "report/mrp_report_bom_structure.xml",
    ],
}
