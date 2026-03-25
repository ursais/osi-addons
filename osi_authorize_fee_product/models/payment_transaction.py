# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    authorize_fee_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Fee Journal Entry",
        readonly=True,
        copy=False,
        help="Journal entry recording the Authorize.net processing fee "
        "for this transaction.",
    )

    def _create_payment(self, **extra_create_values):
        """Extend to record Authorize.net processing fees after payment creation.

        When an Authorize.net payment is confirmed and the provider has a fee
        product with non-zero rates configured, a separate journal entry is
        created that:
          - Debits the fee expense account (from the product)
          - Credits the payment's outstanding receipts account

        The credit is then partially reconciled against the payment's
        outstanding receipts debit so that the remaining balance matches
        the net amount deposited by Authorize.net.
        """
        payment = super()._create_payment(**extra_create_values)

        if (
            self.provider_code != "authorize"
            or not self.provider_id.authorize_fee_product_id
            or self.operation in ("validation", "refund")
        ):
            return payment

        fee_amount = self._compute_authorize_fee()
        if fee_amount <= 0:
            return payment

        self._create_authorize_fee_entry(payment, fee_amount)
        return payment

    def _compute_authorize_fee(self):
        """Calculate the expected Authorize.net processing fee.

        Fee = (transaction_amount * fee_pct / 100) + fee_fixed

        Returns 0 if no rates are configured (allows using the product
        field for manual reconciliation without automatic entries).
        """
        self.ensure_one()
        provider = self.provider_id
        pct = provider.authorize_fee_pct or 0.0
        fixed = provider.authorize_fee_fixed or 0.0
        if not pct and not fixed:
            return 0.0
        raw_fee = abs(self.amount) * (pct / 100.0) + fixed
        fee = round(raw_fee, self.currency_id.decimal_places)
        tx_amount = abs(self.amount)
        if fee >= tx_amount:
            _logger.warning(
                "Computed Authorize.net fee (%.2f) >= transaction amount "
                "(%.2f) for tx %s -- skipping fee entry",
                fee,
                tx_amount,
                self.reference,
            )
            return 0.0
        return fee

    def _create_authorize_fee_entry(self, payment, fee_amount):
        """Create a journal entry for the Authorize.net processing fee.

        The entry debits the fee product's expense account and credits the
        payment journal's outstanding receipts account, then partially
        reconciles the credit against the payment's outstanding line so
        the remaining balance equals the net bank deposit.
        """
        self.ensure_one()
        product = self.provider_id.authorize_fee_product_id
        accounts = product.product_tmpl_id.get_product_accounts(
            fiscal_pos=self.partner_id.property_account_position_id
        )
        expense_account = accounts.get("expense")
        if not expense_account:
            _logger.warning(
                "Authorize.net fee product '%s' (id=%d) has no expense "
                "account configured -- skipping fee entry for tx %s",
                product.display_name,
                product.id,
                self.reference,
            )
            return

        outstanding_account = payment.outstanding_account_id
        if not outstanding_account:
            _logger.warning(
                "Payment %s has no outstanding account -- "
                "skipping fee entry for tx %s",
                payment.display_name,
                self.reference,
            )
            return

        fee_balance = self.currency_id._convert(
            fee_amount,
            self.company_id.currency_id,
            self.company_id,
            payment.date,
        )

        move_vals = {
            "journal_id": payment.journal_id.id,
            "company_id": self.company_id.id,
            "date": payment.date,
            "ref": _("Authorize.net Fee - %s", self.reference),
            "move_type": "entry",
            "line_ids": [
                Command.create(
                    {
                        "account_id": expense_account.id,
                        "partner_id": self.partner_id.commercial_partner_id.id,
                        "name": _(
                            "Authorize.net Processing Fee - %s",
                            self.reference,
                        ),
                        "currency_id": self.currency_id.id,
                        "amount_currency": fee_amount,
                        "balance": fee_balance,
                    }
                ),
                Command.create(
                    {
                        "account_id": outstanding_account.id,
                        "partner_id": self.partner_id.commercial_partner_id.id,
                        "name": _(
                            "Authorize.net Processing Fee - %s",
                            self.reference,
                        ),
                        "currency_id": self.currency_id.id,
                        "amount_currency": -fee_amount,
                        "balance": -fee_balance,
                    }
                ),
            ],
        }

        fee_move = self.env["account.move"].sudo().create(move_vals)
        fee_move.action_post()
        self.authorize_fee_move_id = fee_move

        self._reconcile_fee_with_payment(payment, fee_move, outstanding_account)

        _logger.info(
            "Created Authorize.net fee entry %s (%.2f %s) for tx %s",
            fee_move.name,
            fee_amount,
            self.currency_id.name,
            self.reference,
        )

    def _reconcile_fee_with_payment(
        self, payment, fee_move, outstanding_account
    ):
        """Partially reconcile the fee credit against the payment's
        outstanding receipts debit.

        After reconciliation the payment's outstanding line retains a
        residual equal to (payment_amount - fee), matching the net bank
        deposit from Authorize.net.
        """
        payment_outstanding_lines = payment.move_id.line_ids.filtered(
            lambda l: l.account_id == outstanding_account and not l.reconciled
        )
        fee_outstanding_lines = fee_move.line_ids.filtered(
            lambda l: l.account_id == outstanding_account and not l.reconciled
        )
        lines_to_reconcile = payment_outstanding_lines | fee_outstanding_lines
        if len(lines_to_reconcile) >= 2:
            lines_to_reconcile.reconcile()
