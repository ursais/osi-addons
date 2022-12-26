# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": " Compute time based pricing from Product Attributes",
    "version": "16.0.1.0.0",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": """Automatically Populate Time Based pricing from the Product Attributes.""",
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "sale_temporal",
    ],
    "data": [
        "views/product_template.xml",
        "views/sale_temporal_recurrence_views.xml",
    ],
    "installable": True,
}
