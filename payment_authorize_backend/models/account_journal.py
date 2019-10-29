# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payment_acquirer_id = fields.Many2one(
        'payment.acquirer',
        string='Payment Acquirer',
        copy=False,
    )
    is_electronic_payment_method = fields.Boolean(
        compute='compute_is_electronic_payment_method',
        store=True,
    )

    @api.depends('inbound_payment_method_ids')
    def compute_is_electronic_payment_method(self):
        for journal in self:
            journal.is_electronic_payment_method = journal.inbound_payment_method_ids.filtered(
                lambda p: p.code == 'electronic') and True or False
