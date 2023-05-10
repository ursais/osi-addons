# Copyright (C) 2022, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _default_outbound_payment_methods(self):
        res = super()._default_outbound_payment_methods()
        if self._is_payment_method_available("nacha_ccd"):
            res |= self.env.ref(
                "osi_l10n_us_payment_nacha.account_payment_method_nacha_ccd"
            )
        return res
