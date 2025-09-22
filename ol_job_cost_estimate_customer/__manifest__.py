{
    "name": "Onlogic Sale Estimates Customer",
    "summary": """
        Extends the functionality of your Customers for materials, labour,
        overheads details in job estimation to support a Customer process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_pricing_review",
        "ol_crm_estimate",
        "ol_product_configurator",
        "ol_product_profile",
        "job_cost_estimate_customer",
        "product_configurator_mrp",
        "product_profile",
        "mrp_plm",
    ],
    # always loaded
    "data": [
        "data/product_profile_data.xml",
        "security/ir.model.access.csv",
        "views/mrp_bom.xml",
        "views/sale_estimate_views.xml",
        "wizard/create_product_eco_wizard_view.xml",
        "wizard/quotation_wizard_view.xml",
        "wizard/add_components_wizard_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'ol_job_cost_estimate_customer/static/src/qty_at_date_widget.js',
            'ol_job_cost_estimate_customer/static/src/qty_at_date_widget.xml'
        ],
    },
    "application": False,
    "installable": True,
}
