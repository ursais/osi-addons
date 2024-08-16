{
    "name": "OnLogic Sale Blanket Orders",
    "summary": "Sale Blanket Orders modules related customization",
    "description": """Sale Blanket Orders modules related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_blanket_order",
    ],
    # always loaded
    "data": [
        "data/ir_cron.xml",
        "views/sale_blanket_order_line_views.xml",
    ],
}
