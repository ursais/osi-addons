{
    "name": "LIMS Sign",
    "version": "18.0.1.0.0",
    "summary": "Integrate LIMS with Odoo Sign (electronic signatures)",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/ursais/osi-addons",
    "license": "AGPL-3",
    "category": "LIMS",
    "depends": ["lims", "sign", "documents", "lims_documents"],
    "data": [
        "views/lims_sign_views.xml",
    ],
    "installable": True,
    "application": False,
}
