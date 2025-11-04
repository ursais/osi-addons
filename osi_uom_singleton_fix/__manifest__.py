# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI UoM Singleton Fix",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Fix singleton error in UoM _compute_price method when recordset is empty.
    This fixes ValueError: Expected singleton: uom.uom() errors that occur
    during BOM structure computations when UoM records are missing.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Inventory",
    "depends": ["uom"],
    "data": [],
    "installable": True,
}
