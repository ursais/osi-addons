# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
    Inherit payment.transaction to ensure payment methods are properly set
    from sale order payment method information.
    
    This module fixes the issue where payment transactions are migrated with
    a generic "Payment method" label instead of specific methods like Sofort,
    iDEAL, Card, etc. by properly mapping payment methods from sale orders.
    """

    _inherit = "payment.transaction"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to ensure payment method is set from sale order
        when available.
        """
        transactions = super().create(vals_list)
        for transaction in transactions:
            transaction._set_payment_method_from_sale_order()
        return transactions

    def write(self, vals):
        """
        Override write to update payment method when sale order is linked
        or when sale_order_payment_method_id changes.
        """
        result = super().write(vals)
        if any(
            field in vals
            for field in ["sale_order_ids", "sale_order_payment_method_id"]
        ):
            self._set_payment_method_from_sale_order()
        return result

    def _set_payment_method_from_sale_order(self):
        """
        Set payment_method_id from sale order's payment method information.

        This method attempts to populate the payment_method_id field on
        payment transactions by referencing the sale_order_payment_method_id
        field from related sale orders. This ensures that specific payment
        methods like Sofort, iDEAL, Card, etc. are displayed instead of
        generic "Payment method" labels.
        """
        for transaction in self:
            # Skip if payment method is already set and not generic
            if transaction.payment_method_id:
                method_name = transaction.payment_method_id.name or ""
                if method_name and method_name.lower() not in [
                    "payment method",
                    "payment",
                ]:
                    continue

            # Try to get payment method from sale_order_payment_method_id field
            payment_method = self._get_payment_method_from_sale_order_method(
                transaction
            )

            if payment_method:
                transaction.payment_method_id = payment_method
                _logger.info(
                    "Set payment method for transaction %s: %s",
                    transaction.id,
                    payment_method.name,
                )
            else:
                # Fallback: try to get from sale order's payment method line
                payment_method = self._get_payment_method_from_sale_order(
                    transaction
                )
                if payment_method:
                    transaction.payment_method_id = payment_method
                    _logger.info(
                        "Set payment method for transaction %s from sale order: %s",
                        transaction.id,
                        payment_method.name,
                    )

    def _get_payment_method_from_sale_order_method(self, transaction):
        """
        Get payment method from sale_order_payment_method_id field.

        This method looks up the payment method based on the
        sale_order_payment_method_id field if it exists on the transaction.
        It handles the case where sale_order_payment_method has sub_method_id
        and method_id fields that reference payment method names.

        :param transaction: payment.transaction record
        :return: payment.method record or None
        """
        if not hasattr(transaction, "sale_order_payment_method_id") or not transaction.sale_order_payment_method_id:
            return None

        sale_order_payment_method = transaction.sale_order_payment_method_id

        # Check if sale_order_payment_method has a direct reference to payment.method
        if hasattr(sale_order_payment_method, "payment_method_id") and sale_order_payment_method.payment_method_id:
            return sale_order_payment_method.payment_method_id

        # Handle the case where sale_order_payment_method has sub_method_id and method_id
        # These might reference payment method names or IDs
        payment_method_name = None
        
        # Try sub_method_id first (more specific)
        if hasattr(sale_order_payment_method, "sub_method_id") and sale_order_payment_method.sub_method_id:
            sub_method = sale_order_payment_method.sub_method_id
            if hasattr(sub_method, "name"):
                payment_method_name = sub_method.name
            elif isinstance(sub_method, models.Model) and hasattr(sub_method, "display_name"):
                payment_method_name = sub_method.display_name
        
        # Fallback to method_id if sub_method_id doesn't provide a name
        if not payment_method_name and hasattr(sale_order_payment_method, "method_id") and sale_order_payment_method.method_id:
            method = sale_order_payment_method.method_id
            if hasattr(method, "name"):
                payment_method_name = method.name
            elif isinstance(method, models.Model) and hasattr(method, "display_name"):
                payment_method_name = method.display_name
        
        # If still no name, try the sale_order_payment_method's own name
        if not payment_method_name and hasattr(sale_order_payment_method, "name"):
            payment_method_name = sale_order_payment_method.name

        if payment_method_name:
            # Search for matching payment method by name
            payment_method = self.env["payment.method"].search(
                [
                    ("name", "ilike", payment_method_name),
                ],
                limit=1,
            )
            if payment_method:
                return payment_method

            # Try common mappings for payment method names
            # These mappings handle legacy payment method names
            method_mappings = {
                "net terms": "Payment Terms",
                "credit card prepayment": "Card",
                "credit card": "Card",
                "sofort": "Sofort",
                "ideal": "iDEAL",
            }

            mapped_name = None
            payment_method_name_lower = payment_method_name.lower()
            for key, value in method_mappings.items():
                if key in payment_method_name_lower:
                    mapped_name = value
                    break

            if mapped_name:
                payment_method = self.env["payment.method"].search(
                    [
                        ("name", "ilike", mapped_name),
                    ],
                    limit=1,
                )
                if payment_method:
                    return payment_method

        return None

    def _get_payment_method_from_sale_order(self, transaction):
        """
        Get payment method from related sale order(s).

        This method attempts to find the payment method from the sale order's
        payment method line or payment provider information.

        :param transaction: payment.transaction record
        :return: payment.method record or None
        """
        if not transaction.sale_order_ids:
            return None

        # Get the first sale order (most transactions have one sale order)
        sale_order = transaction.sale_order_ids[0]

        # Try to get payment method from sale order's payment method line
        if hasattr(sale_order, "payment_method_line_id") and sale_order.payment_method_line_id:
            payment_method_line = sale_order.payment_method_line_id
            if hasattr(payment_method_line, "payment_method_id"):
                return payment_method_line.payment_method_id

        # Try to get from sale_order_payment_method_id if it exists on sale order
        if hasattr(sale_order, "sale_order_payment_method_id") and sale_order.sale_order_payment_method_id:
            sale_order_payment_method = sale_order.sale_order_payment_method_id

            # Check if it has a direct reference to payment.method
            if hasattr(sale_order_payment_method, "payment_method_id") and sale_order_payment_method.payment_method_id:
                return sale_order_payment_method.payment_method_id

            # Try to get payment method name from sub_method_id or method_id
            payment_method_name = None
            
            if hasattr(sale_order_payment_method, "sub_method_id") and sale_order_payment_method.sub_method_id:
                sub_method = sale_order_payment_method.sub_method_id
                if hasattr(sub_method, "name"):
                    payment_method_name = sub_method.name
            
            if not payment_method_name and hasattr(sale_order_payment_method, "method_id") and sale_order_payment_method.method_id:
                method = sale_order_payment_method.method_id
                if hasattr(method, "name"):
                    payment_method_name = method.name
            
            if not payment_method_name and hasattr(sale_order_payment_method, "name"):
                payment_method_name = sale_order_payment_method.name

            if payment_method_name:
                payment_method = self.env["payment.method"].search(
                    [
                        ("name", "ilike", payment_method_name),
                    ],
                    limit=1,
                )
                if payment_method:
                    return payment_method

        # Try to get payment method from transaction's provider
        if transaction.provider_id:
            provider = transaction.provider_id
            provider_code = (provider.code or "").lower()
            provider_name = (provider.name or "").lower()

            # Search for payment method that matches the provider
            payment_method = self.env["payment.method"].search(
                [
                    "|",
                    ("code", "ilike", provider_code),
                    ("name", "ilike", provider_name),
                ],
                limit=1,
            )

            if payment_method:
                return payment_method

            # Try common provider code to payment method mappings
            provider_mappings = {
                "sofort": "Sofort",
                "ideal": "iDEAL",
                "stripe": "Card",
                "paypal": "PayPal",
            }

            for code, method_name in provider_mappings.items():
                if code in provider_code or code in provider_name:
                    payment_method = self.env["payment.method"].search(
                        [
                            ("name", "ilike", method_name),
                        ],
                        limit=1,
                    )
                    if payment_method:
                        return payment_method

        return None
