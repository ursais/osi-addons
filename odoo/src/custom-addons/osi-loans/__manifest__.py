# -*- coding: utf-8 -*-
{
    'name': "OSI-Loans",

    'summary': """
        Add new clients, create new applications and run bank statement reviews using the plaid API""",

    'description': """
        This app uses the plaid api for the verification of income and spending of the new loan applicant.
        The user is able to create a new applicant and process the loan application, eventually sending it for
        underwriting where a decision will be made. The funds will then either be direct deposited into the applicant's
        account, or a check will be mailed depending on the option selected at the time of application. An email will be
        sent out to the applicant letting the applicant know the decision made by the underwriter.
    """,

    'author': "OSI Financing",
    'website': "http://richard.ursasys.net:8069/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/create_applicant.xml',
        'views/create_application.xml',
        'views/loan_options.xml',
        'views/contact_override.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True
}
