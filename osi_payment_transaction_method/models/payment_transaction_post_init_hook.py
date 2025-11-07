# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Post-init hook to fix payment methods on existing payment transactions.

    This hook runs after module installation to update existing payment
    transactions that have a generic "Payment method" set, replacing it
    with the correct payment method from their related sale orders.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    PaymentTransaction = env["payment.transaction"]

    # Find payment transactions that need fixing
    # Look for transactions with sale_order_payment_method_id set
    # or transactions linked to sale orders
    transactions_to_fix = PaymentTransaction.search(
        [
            "|",
            ("sale_order_ids", "!=", False),
            ("sale_order_payment_method_id", "!=", False),
        ]
    )

    if transactions_to_fix:
        _logger.info(
            "Fixing payment methods for %d payment transactions",
            len(transactions_to_fix),
        )
        transactions_to_fix._set_payment_method_from_sale_order()
        _logger.info("Completed fixing payment methods for payment transactions")
    else:
        _logger.info("No payment transactions found that need fixing")
