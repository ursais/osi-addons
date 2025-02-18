# Import Odoo libs
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherit Account Move for field/method changes."""

    _inherit = "account.move"

    # METHODS ######

    def unlink(self):
        """
        Restrict deletion of account.move to only the system user
        and users with the special permission.
        Users should cancel account moves instead of deleting to adhere
        to Onlogic Accounting policy.
        """
        for move in self:
            # Allow deletion if the user is the system user to be safe
            # and not impact system operations
            if self.env.uid == 1:
                continue

            # Restrict deletion
            if not self.env.user.has_group("ol_account.group_account_move_delete"):
                raise UserError(
                    _(
                        "You are not allowed to delete account moves. "
                        "Please cancel them instead."
                    )
                )
            if move.state != "draft":
                raise UserError(
                    _(
                        "Only draft account moves can be deleted. "
                        "For posted moves, cancel them instead."
                    )
                )
        return super(AccountMove, self).unlink()

    def _auto_reconcile_deposits(self):
        """
        Automatically reconciles downpayment deposits with their corresponding invoices.
        - Filters invoices of type 'out_invoice'.
        - Identifies related sale orders.
        - Checks for unpaid downpayment invoices.
        - Matches and reconciles downpayment journal items with corresponding invoices.
        """
        for move in self.filtered(lambda m: m.move_type == "out_invoice"):
            so = self.env["sale.order"].search(
                [("invoice_ids", "in", [move.id])], limit=1
            )
            if not so:
                continue

            downpayment_moves = so.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice"
                and inv.payment_state != "paid"
                and inv.id != move.id
            )

            if not downpayment_moves:
                continue

            downpayment_lines = move.line_ids.filtered(lambda line: line.is_downpayment)

            for dp_move in downpayment_moves:
                dp_journal_items = dp_move.line_ids.filtered(
                    lambda line: line.is_downpayment and not line.reconciled
                )

                for dp_line in downpayment_lines:
                    matching_lines = dp_journal_items.filtered(
                        lambda line: line.balance == -dp_line.balance
                        and not line.reconciled
                    )

                    if matching_lines:
                        (matching_lines | dp_line).reconcile()

    def action_post(self):
        result = super().action_post()
        self._auto_reconcile_deposits()
        return result

    # END ##########
