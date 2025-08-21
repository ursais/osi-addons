{
    "name": "OnLogic Fraud Detection",
    "category": "Hidden",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "summary": "Integration with Maxmind Minfraud API",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    "description": "For customer-placed orders, submit information to Maxmind to get a risk score",
    "depends": [
        "ol_base",
        "sale",
        "portal",
        "payment",
    ],
    "data": [
        "data/exception_rule.xml",
        "data/payment_method.xml",
        "views/payment_method.xml",
        "views/sale.xml",
    ],
    "external_dependencies": {
        "python": ["minfraud"],
    },
}
