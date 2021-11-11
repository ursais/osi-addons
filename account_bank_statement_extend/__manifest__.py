# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Account Bank Statement Report Extend",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "category": "account",
    "maintainers": "Open Source Integrators",
    "summary": """OSI Account Bank Statement Report
                Extend Get More Details in Statement Report""",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/account_bank_statement.xml",
        "report/bank_statement_lines_report.xml",
        "wizard/parser_report_bank_statement.xml",
    ],
    "installable": True,
}
