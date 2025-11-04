{
    'name': 'Payment Method Provider Fix',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment',
    'summary': 'Fix payment method provider mappings (PayPal and Stripe)',
    'description': """
Payment Method Provider Fix
============================

This module fixes a data inconsistency issue where:
- PayPal payment method was incorrectly configured to use Stripe provider
- Stripe payment method may have missing provider configuration

The fix ensures that:
- PayPal payment method uses the PayPal provider
- Stripe payment method uses the Stripe provider

This is a one-time fix for data migrated from Odoo v13 to v17.
    """,
    'author': 'Open Source Integrators',
    'website': 'https://github.com/opensourceintegrators',
    'depends': [
        'payment',
        'payment_paypal',
        'payment_stripe',
    ],
    'data': [
        'data/payment_method_fix_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
