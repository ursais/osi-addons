{  # noqa
    "name": "Fulton Accounting Enhancement",
    "summary": "Extends functionality of Accounting.",
    "version": "17.0.1.0.0",
    "author": "Open Source Integrators",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": ["base", "account", "l10n_us_check_printing", "account_check_printing"],
    "data": [
        "views/account_move_line_views.xml",
        "reports/report_payment.xml",
        "reports/print_check_top_report.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
