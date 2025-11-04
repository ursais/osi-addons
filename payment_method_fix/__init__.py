from . import models

def post_init_hook(cr, registry):
    """Run the payment method provider fix after module installation."""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    payment_method = env['payment.method']
    stats = payment_method._fix_provider_mappings()
    
    # Log the results
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info(
        'Payment Method Provider Fix completed: '
        f'PayPal fixed: {stats["paypal_fixed"]}, '
        f'Stripe fixed: {stats["stripe_fixed"]}, '
        f'Errors: {len(stats["errors"])}'
    )
