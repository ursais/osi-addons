# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit="account.invoice"

    # Load all unsold PO lines
    @api.multi
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        res = super(AccountInvoice, self).purchase_order_change()

        # Get Partner Ref from PO
        # Check If reference in PO, if already there append new reference
        if self.purchase_id and self.purchase_id.partner_ref:
            if self.reference and self.reference != self.purchase_id.partner_ref:
                self.reference = self.reference + '; ' + self.purchase_id.partner_ref
            else:
                self.reference = self.purchase_id.partner_ref

        return res

    @api.model
    def default_get(self,default_fields):
        res = super(AccountInvoice, self).default_get(default_fields)

        if res and 'purchase_id' in res:
            po_rec = self.env['purchase.order'].browse(res['purchase_id'])

            # Check If reference in PO, if already there append new reference
            if 'reference' in res and po_rec and po_rec.partner_ref:
                if res['reference'] and res['reference'] != po_rec.partner_ref:
                    res['reference'] = res['reference'] + '; ' + po_rec.partner_ref
                else:
                    res['reference'] = po_rec.partner_ref
        return res

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        purchase_order = self.env['purchase.order'].search([('name','=',self.origin)])
        if purchase_order:
            self.currency_id = purchase_order.currency_id
