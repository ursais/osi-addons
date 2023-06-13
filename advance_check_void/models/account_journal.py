# Copyright (C) 2023 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def get_journal_dashboard_datas(self):
        super().get_journal_dashboard_datas()
        domain_checks_to_print = [
            ("journal_id", "=", self.id),
            ("payment_method_id.code", "=", "check_printing"),
            ("state", "=", "posted"),
            ("is_move_sent", "=", False),
            ("payment_state", "!=", "reversed"),
        ]
        return dict(
            super(AccountJournal, self).get_journal_dashboard_datas(),
            num_checks_to_print=self.env["account.payment"].search_count(
                domain_checks_to_print
            ),
        )
