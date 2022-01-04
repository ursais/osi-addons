# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Documents for lot/tracking number",
    "version": "14.0.1.0.0",
    "category": "Documents",
    "summary": """Manage documents attached to lot/tracking numbers""",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": ["documents", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/documents_folder.xml",
        "data/documents_facet.xml",
        "data/documents_tag.xml",
        "data/documents_workflow_rule.xml",
        "data/res_company.xml",
        "views/res_config_settings.xml",
        "wizards/select_production_lot_view.xml",
    ],
    "maintainers": ["bodedra"],
}
