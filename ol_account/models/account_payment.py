from collections import defaultdict
from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def get_vendor_allocations(self):
        """
        Get vendor related invoices this payment has been applied to and for how much
        """
        self.ensure_one()

        # Get the payable lines for this payment.
        # These are the ones which are reconciled with invoices
        payable_lines = self.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )

        # Reconciliation is done via one or more intermediate journal entries
        intermediate_moves = payable_lines.matched_credit_ids.credit_move_id.move_id

        # Make a mapping between the invoice and how much from this payment was applied
        invoice_map = defaultdict(int)

        for intermediate_move in intermediate_moves:
            # Each intermediate move will be one of:
            # - multiple payment allocations to a single invoice allocation
            # - single payment allocations to a multiple invoice allocation
            # - intermediate_move is the Invoice itself that the payment was applied to
            #    -This usually happens if the user used the Register Button from the Invoice directly or the list view

            payment_allocations = intermediate_move.line_ids.matched_debit_ids
            invoice_allocations = intermediate_move.line_ids.matched_credit_ids

            if intermediate_move.move_type == "in_invoice":
                invoice_map[intermediate_move] += self.get_reconciliation_amount(
                    payment_allocations
                )

        # Turn the invoice mapping into a list of dicts that can be used in the payment email
        allocations = []
        for invoice, payment_amount in invoice_map.items():
            allocations.append(
                {
                    "name": invoice.ref or invoice.name or "",
                    "invoice_amount": invoice.amount_total,
                    "payment_amount": payment_amount,
                }
            )
        return allocations

    @staticmethod
    def get_reconciliation_amount(partial_reconciliations):
        reconciliations_total_amount = sum(partial_reconciliations.mapped("amount"))
        return reconciliations_total_amount
