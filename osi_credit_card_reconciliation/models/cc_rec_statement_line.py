# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class CCRecStatementLine(models.Model):
    _name = "cc.rec.statement.line"
    _description = "Statement Line"

    name = fields.Char('Name', required=True,
                       help="Derived from the related Journal Item.")
    ref = fields.Char('Reference',
                      help="Derived from the related Journal Item.")
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help="Derived from the related Journal Item")
    amount = fields.Float(
        string='Amount', digits=dp.get_precision('Account'),
        help="Derived from the 'debit' amount from related Journal Item.")
    amountcur = fields.Float(
        string='Amount in Currency', digits=dp.get_precision('Account'),
        help="Derived from the 'amount currency' amount from related Journal"
             " Item.")
    date = fields.Date('Date', required=True,
                       help="Derived from related Journal Item.")
    statement_id = fields.Many2one(
        'cc.rec.statement', string='Statement', required=True,
        ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', 'Journal Item',
                                   help="Related Journal Item.")
    cleared_cc_account = fields.Boolean(
        'CC Cleared? ',
        help='Check if the transaction has cleared from the cc')
    research_required = fields.Boolean(
        'Research Required?',
        help='Check if the transaction should be researched by the accounting '
             'team.')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        help="The optional other currency if it is a multi-currency entry.")
    type = fields.Selection([('dr', 'Debit'), ('cr', 'Credit')], 'Cr/Dr')
    from_filter = fields.Boolean('From Filter')

    @api.model
    def create(self, vals):
        # Prevent manually adding new statement line.
        # This would allow only onchange method to pre-populate statement lines
        # based on the filter rules.
        if 'from_filter' in vals and vals['from_filter'] is False:
            raise UserError(_(
                'You cannot add any new bank statement line manually as of '
                'this revision for "%s" !') % vals['name'])
        return super().create(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            # Reset field values in move lines to be added later
            if rec.move_line_id:
                rec.move_line_id.write({
                    'cleared_cc_account': False,
                    'cc_rec_statement_id': False})
            return super(CCRecStatementLine, rec).unlink()
