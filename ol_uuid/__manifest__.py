# pylint: disable=pointless-statement
{
    "name": "OnLogic UUID",
    "summary": "Adds UUID to existing Odoo models.",
    "version": "1.0",
    "depends": [
        "base",
        "account",
        "product",
        "ol_base",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Integrations",
    "description": """Adds UUID to existing Odoo models""",
    "data": [
        "views/sale_order.xml",
        "views/res_partner.xml",
    ],
    "post_init_hook": "_run_install_scripts",
}
