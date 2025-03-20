{
    "name": "Onlogic Accounting",
    "summary": "Accounting Enhancements.",
    "description": """Accounting Enhancements.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Accounting",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "account",
        "sale",
        "account_check_printing",
    ],
    # Data Loaded.
    "data": [
        "security/security.xml",
        "views/res_config_settings_views.xml",
    ],
}
