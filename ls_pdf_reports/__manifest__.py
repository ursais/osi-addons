# pylint: disable=pointless-statement
{
    'name': "PDF Reports",
    'summary': """All OnLogic PDF reports""",
    'description': """
    This module handles all the PDF reports that are attached to emails
    or are printable from the different records.""",
    'onlogic': True,
    'author': "OnLogic",
    'website': "https://www.onlogic.com",
    'category': 'Reporting',
    'version': '17.0.1.0.0',
    'depends': [
        'base',
        'purchase',
        'ol_base',
        # 'ls_base_vat',
        'ls_templates',
        # 'ls_payment_method',
        'ol_account',
        # 'ls_rma_repair_link',
        # 'ls_production_automation',
        # 'ls_coupon_code',
        # 'ls_terms_and_conditions',
        # 'ls_translations',
    ],
    'data': [
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/generic_paperformats.xml',
        # 'reports/invoice_rma_refund.xml',
        # TODO: "helpdesk.rma" model not found
        # 'reports/rma_repair_summary.xml',
        # 'reports/rma_bin_label.xml',
        'reports/mo_bin_label.xml',
        'reports/automation_test.xml',
        'data/purchase_mail_data.xml',
        'views/report_extra_content.xml',
    ],
    "assets": {
        "web.report_assets_common": [
            "/ls_pdf_reports/static/src/scss/*.scss"
        ]
    },
}
