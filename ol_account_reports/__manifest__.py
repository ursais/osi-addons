{
    "onlogic": True,
    "name": "OnLogic Account Report",
    "summary": """Account OnLogic Module """,
    "description": """
        Accounting report Modification report
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "category": "Accounting",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "account_reports",
    ],
    "data": [
        "reports/payment_receipt.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_account_reports/static/src/components/**/*",
        ]
    },
}
