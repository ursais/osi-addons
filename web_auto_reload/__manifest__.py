# See LICENSE file for full copyright and licensing details.

{
    # Module information
    "name": "Web Auto Refresh and Reload",
    "version": "17.0.1.0.1",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "summary": """
        This module essentially provides us a very useful
        feature to refresh the page in given interval.
    """,
    # Author
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    # Dependancies
    "depends": ["web"],
    # Views
    "data": [
        "view/web_auto_refresh_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_auto_reload/static/src/js/auto_refresh.esm.js",
        ],
    },
    # Odoo App Store Specific.
    "images": ["static/description/Banner-Web Auto Refresh and Reload.png"],
    "live_test_url": "https://youtu.be/WoaQILuwxwU",
    # Technical
    "installable": True,
    "auto_install": False,
    "price": 30,
    "currency": "EUR",
}
