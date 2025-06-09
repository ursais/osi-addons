{
    "name": "Dutch EC Sales Report",
    "summary": """
        Extends the functionality of Dutch EC Sales Report .
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Accounting/Localizations/Reporting",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "l10n_nl_intrastat",
    ],
    # always loaded
    "data": [
        "views/action_report_action.xml",
    ],
    "application": False,
    "installable": True,
}
