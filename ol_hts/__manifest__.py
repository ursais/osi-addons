# pylint: disable=pointless-statement
{
    "name": "OnLogic HTS - Replaced by ol_product_tariff",
    "version": "17.0.0.1.0",
    "depends": ["base", "product", "stock", "sale_management"],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Warehouse",
    "description": """
        (378) Use HTS (Harmonized Tariff Codes):

          - Creates HTS object to house codes & code data
          - Add field to product.product for many2one HTS code
          - Create report of HTS codes
    """,
    "demo": [],
    "data": [
        "views/product_template.xml",
        "security/ir.model.access.csv",
        "data/hts_codes.xml",
    ],
}
