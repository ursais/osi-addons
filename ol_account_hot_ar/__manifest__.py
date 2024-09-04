{
    "name": "OnLogic Account Hot AR",
    "summary": "Sale modules related customization",
    "description": """Sale modules related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "account",
    ],
    # always loaded
    "data": [
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/res_partner_views.xml",
        # "data/ir_cron.xml",
    ],
}
