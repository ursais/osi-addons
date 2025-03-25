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
        'views/account_invoice.xml',
        'reports/invoice_generic.xml',
        # TODO: sale.order.payment.method model not found
        # 'reports/invoice_proforma.xml',
        'reports/invoice_proforma_from_so.xml',
        'reports/packing_slip.xml',
        'reports/packing_slip_from_so.xml',
        'reports/picking_list.xml',
        'reports/picking_list_from_so.xml',
        # TODO: "helpdesk.rma" model not found
        # 'reports/rma_repair_summary.xml',
        # 'reports/rma_bin_label.xml',
        'reports/mo_bin_label.xml',
        'reports/sale_order_quote.xml',
        'reports/inventory_sheets.xml',
        'reports/automation_test.xml',
        'reports/purchase_order_doc.xml',
        'reports/product_labels.xml',
        'reports/inventory_label.xml',
        'data/purchase_mail_data.xml',
        'views/report_extra_content.xml',
    ],
    "assets": {
        "web.report_assets_common": [
            "/ls_pdf_reports/static/src/scss/*.scss"
        ]
    },
}
