{
    "name": "Onlogic PDF Reports",
    "summary": """All OnLogic PDF reports""",
    "description": """
    This module handles all the PDF reports that are attached to emails
    or are printable from the different records.""",
    "onlogic": True,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "category": "Reporting",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base",
        "purchase",
        "ol_base",
        "ol_templates",
        "ol_account",
    ],
    "data": [
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/report_extra_content.xml",
    ],
    "assets": {
        "web.report_assets_common": ["/ol_pdf_reports/static/src/scss/*.scss"],
        "web.report_assets_pdf": ["/ol_pdf_reports/static/src/scss/*.scss"],
    },
}
