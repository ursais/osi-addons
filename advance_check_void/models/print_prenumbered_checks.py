# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from odoo import models, _


class PrintPreNumberedChecks(models.TransientModel):
    _inherit = 'print.prenumbered.checks'

    def print_checks(self):
        check_number = int(self.next_check_number)
        number_len = len(self.next_check_number or "")
        payments = self.env['account.payment'].browse(self.env.context['payment_ids'])
        payments.filtered(lambda r: r.state == 'draft').action_post()
        payments.filtered(lambda r: r.state == 'posted' and not r.is_move_sent).write({'is_move_sent': True})
        for payment in payments:
            bills_per_check = self.env['ir.config_parameter'].sudo().get_param('advance_check_void.bills_per_check') or 9
            payment.check_number = '%0{}d'.format(number_len) % check_number
            check_number += (math.ceil(len(payment.reconciled_bill_ids) / bills_per_check) or 1)
        return payments.do_print_checks()
