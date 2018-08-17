# -*- coding: utf-8 -*-
# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice Line')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line,part)

        # make sure the account move line gets the invoice line id        
        res.update({'invl_id': line.get('invl_id', False)})
        return res
    
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        discount_total = 0.0
        
        # Calculate total discount and modify existing move_lines to add discount amounts
        for line in self.invoice_line_ids:
        
            # check for discount on the invoice line
            if line.discount_amt:
                # browse move lines
                for move_line in move_lines:
                
                    # identify the moveline related to the invoice line
                    if move_line[2].get('invl_id',False) == line.id:
                    
                        # adjust value in the existing move_line by the discount amount
                        if self.type == 'out_refund':
                            value = move_line[2].get('debit', 0.0) + line.discount_amt
                            move_line[2].update({'debit': value})
                        elif self.type == 'out_invoice':    
                            value = move_line[2].get('credit', 0.0) + line.discount_amt
                            move_line[2].update({'credit': value})
                            
                        # add discount so we can write an extra move line for the discount
                        discount_total += line.discount_amt
        
        # create the extra move line for the discount
        if discount_total:
            # prepare vals for discount move line
            discount_line = self.move_line_get_discount(discount_total)
            # append move line to existing record
            move_lines.insert(0, (0, 0, discount_line))
        
        return move_lines
        
    @api.model
    def move_line_get_discount(self, discount_total):
        # Fetch Discount Account from company
        acc_discount_id = self.company_id.account_discount_id and self.company_id.account_discount_id.id or False
        if not acc_discount_id:
            raise ValidationError(_("Please set Discount Account in company configuration!"))
        return {
            'type': 'src',
            'name': 'Discount',
            'price_unit': discount_total,
            'debit':self.type=="out_invoice" and discount_total or False,
            'credit':self.type=="out_refund" and discount_total or False,
            'quantity': 1,
            'price': discount_total,
            'account_id': acc_discount_id,
            'product_id': False,
            'uos_id': False,
            'account_analytic_id': False,
        }
