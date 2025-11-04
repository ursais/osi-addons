# -*- coding: utf-8 -*-

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentMethod(models.Model):
    """Extend payment.method to fix provider assignments on module installation."""

    _inherit = 'payment.method'

    @api.model
    def _fix_provider_mappings(self):
        """
        Fix payment method provider mappings.

        This method corrects the data inconsistency where:
        - PayPal payment method incorrectly points to Stripe provider
        - Stripe payment method may have incorrect or missing provider

        The fix:
        1. Finds all payment methods that have Stripe provider but should have PayPal
        2. Finds all payment methods that should have Stripe provider
        3. Corrects the provider assignments

        Returns:
            dict: Statistics about the fix operation
        """
        PaymentProvider = self.env['payment.provider']
        stats = {
            'paypal_fixed': 0,
            'stripe_fixed': 0,
            'paypal_removed_from_stripe': 0,
            'errors': []
        }

        try:
            # Find PayPal provider
            paypal_provider = PaymentProvider.search([
                ('code', '=', 'paypal')
            ], limit=1)

            # Find Stripe provider
            stripe_provider = PaymentProvider.search([
                ('code', '=', 'stripe')
            ], limit=1)

            if not paypal_provider:
                _logger.warning(
                    'Payment Method Provider Fix: PayPal provider not found. '
                    'Make sure payment_paypal module is installed.'
                )
                stats['errors'].append('PayPal provider not found')
            if not stripe_provider:
                _logger.warning(
                    'Payment Method Provider Fix: Stripe provider not found. '
                    'Make sure payment_stripe module is installed.'
                )
                stats['errors'].append('Stripe provider not found')

            # Fix payment methods that incorrectly have Stripe but should have PayPal
            # This addresses the main issue: PayPal payment method showing Stripe provider
            if paypal_provider and stripe_provider:
                # Find payment methods that have Stripe provider but should be PayPal
                # We'll look for methods that have Stripe but not PayPal
                methods_with_stripe = self.search([
                    ('provider_ids', 'in', [stripe_provider.id])
                ])

                for method in methods_with_stripe:
                    has_paypal = paypal_provider in method.provider_ids
                    has_stripe = stripe_provider in method.provider_ids

                    # If method has Stripe but not PayPal, and it's a PayPal-related method
                    # Check by code or name (PayPal methods often have 'paypal' in code/name)
                    method_code = (method.code or '').lower()
                    method_name = (method.name or '').lower()
                    
                    is_paypal_method = 'paypal' in method_code or 'paypal' in method_name
                    is_stripe_method = 'stripe' in method_code or 'stripe' in method_name

                    # If this looks like a PayPal method but has Stripe provider
                    if is_paypal_method and has_stripe and not has_paypal:
                        # Remove Stripe and add PayPal
                        method.provider_ids = [(3, stripe_provider.id), (4, paypal_provider.id)]
                        stats['paypal_fixed'] += 1
                        _logger.info(
                            f'Payment Method Provider Fix: Fixed PayPal method '
                            f'"{method.name}" (code: {method.code}) - removed Stripe, added PayPal'
                        )
                    # If it's a PayPal method that has both (incorrect), remove Stripe
                    elif is_paypal_method and has_stripe and has_paypal:
                        method.provider_ids = [(3, stripe_provider.id)]
                        stats['paypal_removed_from_stripe'] += 1
                        _logger.info(
                            f'Payment Method Provider Fix: Removed Stripe from PayPal method '
                            f'"{method.name}" (code: {method.code})'
                        )
                    # If it's a Stripe method but doesn't have Stripe provider
                    elif is_stripe_method and not has_stripe:
                        # Add Stripe provider
                        if paypal_provider in method.provider_ids:
                            method.provider_ids = [(3, paypal_provider.id), (4, stripe_provider.id)]
                        else:
                            method.provider_ids = [(4, stripe_provider.id)]
                        stats['stripe_fixed'] += 1
                        _logger.info(
                            f'Payment Method Provider Fix: Fixed Stripe method '
                            f'"{method.name}" (code: {method.code}) - added Stripe provider'
                        )
                    # If it's a Stripe method that has PayPal but not Stripe (wrong)
                    elif is_stripe_method and has_paypal and not has_stripe:
                        method.provider_ids = [(3, paypal_provider.id), (4, stripe_provider.id)]
                        stats['stripe_fixed'] += 1
                        _logger.info(
                            f'Payment Method Provider Fix: Fixed Stripe method '
                            f'"{method.name}" (code: {method.code}) - removed PayPal, added Stripe'
                        )

            # Also handle cases where payment methods are searched by exact code match
            # Some payment methods might have codes exactly matching provider codes
            if paypal_provider:
                paypal_method_by_code = self.search([
                    ('code', '=', 'paypal')
                ], limit=1)
                
                if paypal_method_by_code:
                    if stripe_provider and stripe_provider in paypal_method_by_code.provider_ids:
                        # Remove Stripe if present
                        paypal_method_by_code.provider_ids = [(3, stripe_provider.id)]
                        _logger.info(
                            'Payment Method Provider Fix: Removed Stripe from payment method '
                            'with code="paypal"'
                        )
                    if paypal_provider not in paypal_method_by_code.provider_ids:
                        paypal_method_by_code.provider_ids = [(4, paypal_provider.id)]
                        if stats['paypal_fixed'] == 0:  # Only count if not already counted
                            stats['paypal_fixed'] += 1
                        _logger.info(
                            'Payment Method Provider Fix: Added PayPal provider to payment method '
                            'with code="paypal"'
                        )

            if stripe_provider:
                stripe_method_by_code = self.search([
                    ('code', '=', 'stripe')
                ], limit=1)
                
                if stripe_method_by_code:
                    if paypal_provider and paypal_provider in stripe_method_by_code.provider_ids:
                        # Remove PayPal if present
                        stripe_method_by_code.provider_ids = [(3, paypal_provider.id)]
                        _logger.info(
                            'Payment Method Provider Fix: Removed PayPal from payment method '
                            'with code="stripe"'
                        )
                    if stripe_provider not in stripe_method_by_code.provider_ids:
                        stripe_method_by_code.provider_ids = [(4, stripe_provider.id)]
                        if stats['stripe_fixed'] == 0:  # Only count if not already counted
                            stats['stripe_fixed'] += 1
                        _logger.info(
                            'Payment Method Provider Fix: Added Stripe provider to payment method '
                            'with code="stripe"'
                        )

        except Exception as e:
            error_msg = f'Error fixing payment method provider mappings: {str(e)}'
            _logger.error(error_msg, exc_info=True)
            stats['errors'].append(error_msg)

        return stats
