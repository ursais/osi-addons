# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    in_payment_journal_id = fields.Many2one(
        "account.journal", string="Customer Payment Journal",
        domain=[('type', 'in', ('bank', 'cash'))])
    in_payment_method_id = fields.Many2one(
        "account.payment.method", string="Customer Payment Method")
    out_payment_journal_id = fields.Many2one(
        "account.journal", string="Vendor Payment Journal",
        domain=[('type', 'in', ('bank', 'cash'))])
    out_payment_method_id = fields.Many2one(
        "account.payment.method", string="Vendor Payment Method")

    @api.multi
    @api.onchange('in_payment_journal_id')
    def onchange_in_payment_journal(self):
        for rec in self:
            ids = rec.in_payment_journal_id.inbound_payment_method_ids.ids \
                or False
            return {'domain': {'in_payment_method_id': [('id', 'in', ids)]}}

    @api.multi
    @api.onchange('out_payment_journal_id')
    def onchange_out_payment_journal(self):
        for rec in self:
            ids = rec.out_payment_journal_id.outbound_payment_method_ids.ids \
                or False
            return {'domain': {'out_payment_method_id': [('id', 'in', ids)]}}
