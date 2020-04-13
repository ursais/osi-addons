# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_journal_id = fields.Many2one(
        "account.journal", string="Payment Journal",
        domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one(
        "account.payment.method", string="Payment Method")

    @api.multi
    @api.onchange('partner_id')
    def onchange_payment_info(self):
        for rec in self:
            if rec.partner_id:
                rec.payment_journal_id = \
                    rec.partner_id.out_payment_journal_id.id or False
                rec.payment_method_id = \
                    rec.partner_id.out_payment_method_id.id or False

    @api.multi
    @api.onchange('payment_journal_id')
    def onchange_payment_journal(self):
        for rec in self:
            ids = rec.payment_journal_id.outbound_payment_method_ids.ids \
                or False
            return {'domain': {'payment_method_id': [('id', 'in', ids)]}}
