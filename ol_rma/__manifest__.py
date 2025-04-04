{
    "name": "OnLogic RMA Customization",
    "summary": "Adds OnLogic RMA Customization",
    "description": """Adds OnLogic RMA Customization""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "RMA",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_templates",
        # "rma",
    ],
    # always loaded
    "data": [
        # 'reports/invoice_rma_refund.xml',
        # TODO: NC : "helpdesk.rma" model not found
        # 'reports/rma_repair_summary.xml',
        # 'reports/rma_bin_label.xml',
    ],
}
