from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    """Inherit Account Payment for field/method changes."""

    _inherit = "account.payment"

    # METHODS ######

    def print_checks(self):
        """Overridden the method to modification of bypass the checking the check number for Customer Payment."""
        """Check that the recordset is valid, set the payments state to sent and call print_checks()"""
        # Since this method can be called via a client_action_multi, we need to make sure the received records are what we expect
        self = self.filtered(
            lambda r: r.payment_method_line_id.code == "check_printing"
            and r.state != "reconciled"
        )

        if len(self) == 0:
            raise UserError(
                _(
                    "Payments to print as a checks must have 'Check' selected as payment method and "
                    "not have already been reconciled"
                )
            )
        if any(payment.journal_id != self[0].journal_id for payment in self):
            raise UserError(
                _(
                    "In order to print multiple checks at once, they must belong to the same bank journal."
                )
            )

        if not self[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first pre-printed check
            # so payments are attributed the number of the check the'll be printed on.
            self.env.cr.execute(
                """
                  SELECT payment.id
                    FROM account_payment payment
                    JOIN account_move move ON movE.id = payment.move_id
                   WHERE journal_id = %(journal_id)s and payment_type = 'outbound'
                   AND payment.check_number IS NOT NULL
                ORDER BY payment.check_number::BIGINT DESC
                   LIMIT 1
            """,
                {
                    "journal_id": self.journal_id.id,
                },
            )
            last_printed_check = self.browse(self.env.cr.fetchone())
            number_len = len(last_printed_check.check_number or "")
            next_check_number = "%0{}d".format(number_len) % (
                int(last_printed_check.check_number) + 1
            )

            return {
                "name": _("Print Pre-numbered Checks"),
                "type": "ir.actions.act_window",
                "res_model": "print.prenumbered.checks",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "payment_ids": self.ids,
                    "default_next_check_number": next_check_number,
                },
            }
        else:
            self.filtered(lambda r: r.state == "draft").action_post()
            return self.do_print_checks()
