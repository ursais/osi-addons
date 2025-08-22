{
    "name": "OnLogic Bank Tranfer Email",
    "summary": "Sale modules related Email Template",
    "description": """Sale modules related Email Template.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_templates",
        "ol_fraud_detection",
        "sale",
        "ol_sale",
        "ol_sale_substate",
    ],
    # always loaded
    "data": [
        "data/bank_transfer_email.xml",
        "views/payment_method_view.xml",
    ],
}
