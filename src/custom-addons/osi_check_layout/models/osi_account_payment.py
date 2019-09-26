# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def do_print_checks(self):
        us_check_layout = self[0].company_id.us_check_layout
        if us_check_layout != 'disabled':
            self.write({'state': 'sent'})
            return self.env.ref(us_check_layout).report_action(self)
        return super(AccountPayment, self).do_print_checks()
