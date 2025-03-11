# pylint: disable=pointless-statement
{
    "name": "OnLogic Developer Tools",
    "summary": "Super Secret Tools for Tweaking Data",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": [
        "ol_base",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_dev_tools/static/src/js/debug.js",
        ],
    },
}
