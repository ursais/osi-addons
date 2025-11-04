# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    """Inherit account.payment to fix payment method assignment."""

    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure payment method is properly set."""
        payments = super().create(vals_list)
        for payment in payments:
            payment._fix_payment_method()
        return payments

    def write(self, vals):
        """Override write to fix payment method when relevant fields change."""
        result = super().write(vals)
        if any(field in vals for field in ["payment_provider_id", "payment_method_line_id", "payment_type"]):
            self._fix_payment_method()
        return result

    def _fix_payment_method(self):
        """
        Fix payment method assignment based on payment provider and transaction details.
        
        This method ensures that payment methods are correctly mapped from payment
        provider information instead of using generic default values.
        """
        for payment in self:
            # Skip if payment method is already set and not generic
            # Check if payment method name is the generic "Payment method"
            if payment.payment_method_line_id:
                method_name = payment.payment_method_line_id.name or ""
                if method_name and method_name.lower() not in ["payment method", "payment"]:
                    continue

            # Try to get payment method from payment provider
            payment_method = self._get_payment_method_from_provider(payment)
            
            if payment_method:
                payment.payment_method_line_id = payment_method
                _logger.info(
                    "Fixed payment method for payment %s: %s",
                    payment.id,
                    payment_method.name,
                )
            else:
                # Try to get payment method from payment transaction
                payment_method = self._get_payment_method_from_transaction(payment)
                if payment_method:
                    payment.payment_method_line_id = payment_method
                    _logger.info(
                        "Fixed payment method for payment %s from transaction: %s",
                        payment.id,
                        payment_method.name,
                    )

    def _get_payment_method_from_provider(self, payment):
        """
        Get payment method from payment provider information.
        
        :param payment: account.payment record
        :return: account.payment.method.line record or None
        """
        if not payment.payment_provider_id:
            return None

        provider = payment.payment_provider_id
        journal = payment.journal_id
        
        if not journal:
            return None

        # Determine which payment method lines to search based on payment type
        if payment.payment_type == "inbound":
            method_lines = journal.inbound_payment_method_line_ids
        elif payment.payment_type == "outbound":
            method_lines = journal.outbound_payment_method_line_ids
        else:
            method_lines = journal.inbound_payment_method_line_ids

        if not method_lines:
            return None

        # Get payment method line from journal based on provider code
        # Payment providers typically have codes like 'sofort', 'ideal', etc.
        provider_code = provider.code or ""
        provider_code_lower = provider_code.lower()

        # Search for payment method lines that match the provider
        payment_method_lines = method_lines.filtered(
            lambda line: line.payment_method_id.code
            and provider_code_lower in line.payment_method_id.code.lower()
        )

        if payment_method_lines:
            return payment_method_lines[0]

        # Try matching by provider name
        provider_name = provider.name or ""
        provider_name_lower = provider_name.lower()

        # Common payment method mappings
        method_mappings = {
            "sofort": ["sofort"],
            "ideal": ["ideal"],
            "card": ["card", "credit", "debit"],
            "sepa": ["sepa", "direct debit"],
            "paypal": ["paypal"],
            "stripe": ["card", "stripe"],
        }

        # Find matching payment method
        for key, keywords in method_mappings.items():
            if any(keyword in provider_name_lower or keyword in provider_code_lower for keyword in keywords):
                matching_lines = method_lines.filtered(
                    lambda line: line.payment_method_id.code
                    and any(
                        keyword in line.payment_method_id.code.lower()
                        for keyword in keywords
                    )
                )
                if matching_lines:
                    return matching_lines[0]

        return None

    def _get_payment_method_from_transaction(self, payment):
        """
        Get payment method from related payment transaction.
        
        :param payment: account.payment record
        :return: account.payment.method.line record or None
        """
        # Try to find related payment transaction
        transaction = self.env["payment.transaction"].search(
            [
                ("payment_id", "=", payment.id),
            ],
            limit=1,
        )

        if not transaction:
            # Try to find by reference
            if payment.ref:
                transaction = self.env["payment.transaction"].search(
                    [
                        ("reference", "=", payment.ref),
                    ],
                    limit=1,
                )

        if transaction and transaction.provider_id:
            # Use the provider from transaction to find the matching payment method
            provider = transaction.provider_id
            journal = payment.journal_id
            
            if not journal:
                return None

            # Determine which payment method lines to search based on payment type
            if payment.payment_type == "inbound":
                method_lines = journal.inbound_payment_method_line_ids
            elif payment.payment_type == "outbound":
                method_lines = journal.outbound_payment_method_line_ids
            else:
                method_lines = journal.inbound_payment_method_line_ids

            if not method_lines:
                return None

            # Get provider code and name
            provider_code = provider.code or ""
            provider_code_lower = provider_code.lower()
            provider_name = provider.name or ""
            provider_name_lower = provider_name.lower()

            # Search for payment method lines that match the provider
            payment_method_lines = method_lines.filtered(
                lambda line: line.payment_method_id.code
                and (provider_code_lower in line.payment_method_id.code.lower()
                     or provider_name_lower in (line.payment_method_id.name or "").lower())
            )

            if payment_method_lines:
                return payment_method_lines[0]

            # Try matching with common payment method mappings
            method_mappings = {
                "sofort": ["sofort"],
                "ideal": ["ideal"],
                "card": ["card", "credit", "debit"],
                "sepa": ["sepa", "direct debit"],
                "paypal": ["paypal"],
                "stripe": ["card", "stripe"],
            }

            for key, keywords in method_mappings.items():
                if any(keyword in provider_name_lower or keyword in provider_code_lower for keyword in keywords):
                    matching_lines = method_lines.filtered(
                        lambda line: line.payment_method_id.code
                        and any(
                            keyword in line.payment_method_id.code.lower()
                            for keyword in keywords
                        )
                    )
                    if matching_lines:
                        return matching_lines[0]

        return None
