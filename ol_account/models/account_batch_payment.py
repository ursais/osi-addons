# Copyright 2025, AUTHOR(S)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def action_send_detailed_payment_emails(self):
        for batch in self:
            for payment in batch.payment_ids:
                if payment.partner_id and not payment.partner_id.ar:
                    raise ValidationError(
                        _("AR is not set on : %s in batch: %s")
                        % (payment.partner_id.display_name, batch.name)
                    )

        return super().action_send_detailed_payment_emails()
