{
    "name": "LIMS Documents Integration",
    "version": "18.0.1.0.0",
    "summary": "Integrate LIMS with Odoo Documents (Enterprise)",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/ursais/osi-addons",
    "license": "AGPL-3",
    "category": "LIMS",
    "depends": ["lims", "documents"],
    "data": [
        "security/ir.model.access.csv",
        "views/lims_documents_views.xml",
    ],
    "installable": True,
    "application": False,
}
