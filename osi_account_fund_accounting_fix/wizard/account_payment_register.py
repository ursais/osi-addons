# Copyright (c) 2025 OSI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models

NO_FUND_KEY = ("no_fund",)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _reconcile_payments_by_fund_groups(
        self, payment, payment_lines, lines, extra_context
    ):
        """Fix two bugs in the original fund-group reconciliation:

        1. ``sorted(pay_keys, ...)`` crashes with ``TypeError: '<' not
           supported between instances of 'tuple' and 'str'`` when
           ``pay_keys`` contains both ``("no_fund",)`` (a tuple of str)
           and fund keys like ``(('42', 100.0),)`` (a tuple of tuple).
           Fixed by using ``str(k)`` as the sort key so all elements are
           comparable.

        2. ``"no_fund" in pay_keys`` always evaluates to ``False``
           because ``pay_keys`` is a set of tuples, not strings.
           Fixed by checking for the actual tuple key ``("no_fund",)``.
        """
        if len(payment_lines) <= 1:
            return False

        domain_reconcile = [
            ("reconciled", "=", False),
            ("parent_state", "=", "posted"),
        ]

        for account in payment_lines.account_id:
            pay_amls = payment_lines.filtered(lambda l: l.account_id == account)
            inv_amls = lines.filtered(lambda l: l.account_id == account)
            if len(pay_amls) <= 1:
                (pay_amls + inv_amls).with_context(**extra_context).filtered_domain(
                    [("account_id", "=", account.id)] + domain_reconcile
                ).reconcile()
                continue

            pay_keys = {
                self._fund_key_for_reconcile_group(pl) for pl in pay_amls
            }
            inv_keys = {
                self._fund_key_for_reconcile_group(il) for il in inv_amls
            }

            has_no_fund = NO_FUND_KEY in pay_keys
            if pay_keys != inv_keys or (has_no_fund and len(pay_keys) > 1):
                (pay_amls + inv_amls).with_context(**extra_context).filtered_domain(
                    [("account_id", "=", account.id)] + domain_reconcile
                ).reconcile()
                continue

            for fk in sorted(pay_keys, key=lambda k: str(k)):
                pl_group = pay_amls.filtered(
                    lambda l, fk=fk: self._fund_key_for_reconcile_group(l)
                    == fk
                )
                inv_group = inv_amls.filtered(
                    lambda l, fk=fk: self._fund_key_for_reconcile_group(l)
                    == fk
                )
                if not pl_group or not inv_group:
                    (pay_amls + inv_amls).with_context(
                        **extra_context
                    ).filtered_domain(
                        [("account_id", "=", account.id)] + domain_reconcile
                    ).reconcile()
                    break
                (pl_group + inv_group).with_context(
                    **extra_context
                ).filtered_domain(
                    [("account_id", "=", account.id)] + domain_reconcile
                ).reconcile()
        return True
