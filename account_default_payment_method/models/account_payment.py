# Copyright (c) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.payment"

    @api.multi
    @api.onchange('partner_id', 'payment_type')
    def onchange_payment_info(self):
        for rec in self:
            # Customer Payment
            if rec.payment_type == 'inbound' and rec.partner_id:
                rec.journal_id = \
                    rec.partner_id.in_payment_journal_id.id or False
                rec.payment_method_id = \
                    rec.partner_id.in_payment_method_id.id or False
            # Vendor Payment
            if rec.payment_type == 'outbound' and rec.partner_id:
                rec.journal_id = \
                    rec.partner_id.out_payment_journal_id.id or False
                rec.payment_method_id = \
                    rec.partner_id.out_payment_method_id.id or False
