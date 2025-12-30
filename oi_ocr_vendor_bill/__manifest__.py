# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI OCR Vendor Bill",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    OCR functionality for vendor bills using Tesseract OCR engine.
    Automatically extracts text from vendor bill images and populates invoice fields.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Accounting",
    "depends": ["account"],
    "external_dependencies": {
        "python": ["pytesseract", "Pillow"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
