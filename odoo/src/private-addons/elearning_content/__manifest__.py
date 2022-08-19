# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Elearning Content",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Training Content and Documentation",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "depends": ["website_slides"],
    "data": [
        "data/slide.channel.csv",
        "data/slide.slide.csv",
        # Odoo Interface
        "data/00-interface/slide.slide.xml",
        # Accounting
        # Inventory
        # Manufacturing
        # Service
        # Purchase
        # Sales / CRM
        # Website
        # Human Resources
        # Administration
        # Development
    ],
    "application": True,
    "maintainers": ["ursais"],
}
