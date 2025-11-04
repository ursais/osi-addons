# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Inherit payment.transaction to ensure payment methods are set on related payments."""

    _inherit = "payment.transaction"

    def _create_payment(self, amount=None, extra_vals=None):
        """
        Override to ensure payment method is set when creating payment from transaction.
        
        :param amount: payment amount (optional)
        :param extra_vals: extra values for payment creation (optional)
        :return: account.payment record
        """
        payment = super()._create_payment(amount=amount, extra_vals=extra_vals)
        
        if payment:
            # Fix payment method after creation
            payment._fix_payment_method()
        
        return payment

    def _update_payment(self, payment):
        """
        Override to ensure payment method is updated when transaction is updated.
        
        :param payment: account.payment record
        """
        super()._update_payment(payment)
        
        if payment:
            # Fix payment method after update
            payment._fix_payment_method()
