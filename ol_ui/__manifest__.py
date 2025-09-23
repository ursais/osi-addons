# pylint: disable=pointless-statement
{
    "name": "OnLogic UI",
    "summary": "OnLogic User Interface Customizations",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "description": """OnLogic User Interface Customizations""",
    "onlogic": True,
    "category": "Tools",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": [
        "web",
        "ol_base",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_ui/static/src/js/domain_selector.js",
        ]
    },
}
