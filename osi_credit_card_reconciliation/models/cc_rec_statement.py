# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import time
from operator import itemgetter
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class CcRecStatement(models.Model):
    _name = "cc.rec.statement"
    _description = 'CC Rec Statement'
    _order = "ending_date desc"

    def check_group(self):
        """Check if following security constraints are implemented for groups:
        CC Statement Preparer– they can create, view and delete any of the Bank
         Statements provided the Bank Statement is not in the DONE state,
        or the Ready for Review state.
        Bank Statement Verifier – they can create, view, edit, and delete any
         of the Bank Statements information at any time.
        NOTE: DONE Bank Statements  are only allowed to be deleted by a Bank
         Statement Verifier."""

        group_verifier_id = self.env['ir.model.data'].xmlid_to_res_id(
            'osi_credit_card_reconciliation.group_cc_stmt_verifier')
        if group_verifier_id:
            group_verifier = self.env['res.groups'].browse(group_verifier_id)
            group_user_ids = [user.id for user in group_verifier.users]
            for statement in self:
                if statement.state != 'draft' and self._uid not in \
                        group_user_ids:
                    raise UserError(
                        _("Only a member of '%s' group can delete/edit credit"
                          " card statements when not in the draft state!" %
                          (group_verifier.name)))
        return True

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update({
            'credit_move_line_ids': [],
            'debit_move_line_ids': [],
            'name': ''})
        return super().copy(default)

    @api.multi
    def write(self, vals):
        for rec in self:
            # Check if the user is allowed to perform the action
            rec.check_group()
            if 'journal_id' in vals and vals.get('journal_id'):
                journal = self.env['account.journal'].browse(
                    vals.get('journal_id'))
                if journal and journal.partner_id and \
                        journal.partner_id.property_account_payable_id:
                    vals.update({
                        'account_id':
                            journal.partner_id.property_account_payable_id.id})
            return super(CcRecStatement, rec).write(vals)

    @api.model
    def create(self, vals):
        if 'journal_id' in vals and vals.get('journal_id'):
            journal = self.env['account.journal'].browse(
                vals.get('journal_id'))
            if journal and journal.partner_id and \
                    journal.partner_id.property_account_payable_id:
                vals.update({
                    'account_id':
                        journal.partner_id.property_account_payable_id.id})
        return super(CcRecStatement, self).create(vals)

    @api.multi
    def unlink(self):
        # Reset the related account.move.line to be re-assigned later to
        # statement.
        # Check if the user is allowed to perform the action
        self.check_group()
        for rec in self:
            lines = rec.credit_move_line_ids + rec.debit_move_line_ids
            # call unlink method to reset
            lines.unlink()
            return super(CcRecStatement, rec).unlink()

    def _check_difference_balance(self):
        "Check if difference balance is zero or not."
        for statement in self:
            if statement.cleared_balance_cur:
                if statement.difference_cur != 0.0:
                    raise UserError(_(
                        "Prior to reconciling a statement, all differences "
                        "must be accounted for and the difference must be "
                        "zero. Please review and make necessary changes."))
            else:
                if statement.difference != 0.0:
                    raise UserError(_(
                        "Prior to reconciling a statement, all differences "
                        "must be accounted for and the difference must be "
                        "zero. Please review and make necessary changes."))
        return True

    @api.multi
    def action_cancel(self):
        "Cancel the statement."
        for rec in self:
            rec.write({'state': 'cancel'})
        return True

    @api.multi
    def action_review(self):
        # Change the status of statement from 'draft' to 'to_be_reviewed'."
        # If difference balance not zero prevent further processing
        for rec in self:
            rec._check_difference_balance()
            rec.write({'state': 'to_be_reviewed'})
        return True

    @api.multi
    def action_process(self):
        # Set the account move lines as Cleared and Assign CC Acc Rec
        # Statement ID for the statement lines which are marked as Cleared.
        # If difference balance not zero prevent further processing
        self._check_difference_balance()
        for rec in self:
            lines = rec.credit_move_line_ids + rec.debit_move_line_ids
            for line in lines:
                # Mark the move lines as 'Cleared' and assign the
                # 'CC Acc Rec Statement ID'
                line.move_line_id.write({
                    'cleared_cc_account': line.cleared_cc_account,
                    'cc_rec_statement_id':
                        line.cleared_cc_account and rec.id or False})
            rec.write({'state': 'done',
                       'verified_by_user_id': self._uid,
                       'verified_date': time.strftime('%Y-%m-%d')})
        return True

    @api.multi
    def action_cancel_draft(self):
        """Reset the statement to draft and perform resetting operations."""
        aml = self.env['account.move.line']
        sline = self.env['cc.rec.statement.line']
        for rec in self:
            lines = rec.credit_move_line_ids + rec.debit_move_line_ids
            for line in lines:
                sline |= line

                # Find move lines related to statement lines
                if line.move_line_id:
                    aml |= line.move_line_id

            # Reset 'Cleared' and 'CC Acc Rec Statement ID' to False
            aml.write({'cleared_cc_account': False,
                       'cc_rec_statement_id': False})
            # Reset 'Cleared' in statement lines
            sline.write({'cleared_cc_account': False,
                         'research_required': False})
            # Reset statement
            rec.write({'state': 'draft',
                       'verified_by_user_id': False,
                       'verified_date': False})
        return True

    @api.multi
    def action_select_all(self):
        """Mark all the statement lines as 'Cleared'."""
        line_ids = self.env['cc.rec.statement.line']
        for rec in self:
            lines = rec.credit_move_line_ids + rec.debit_move_line_ids
            line_ids |= map(lambda x: x.id, lines)
            line_ids.write({'cleared_cc_account': True})
        return True

    @api.multi
    def action_unselect_all(self):
        """Reset 'Cleared' in all the statement lines."""
        line_ids = self.env['cc.rec.statement.line']
        for rec in self:
            lines = rec.credit_move_line_ids + rec.debit_move_line_ids
            line_ids |= map(lambda x: x.id, lines)
            line_ids.write({'cleared_cc_account': False})
        return True

    # refresh data
    @api.multi
    def refresh_record(self):
        retval = True
        refdict = {}
        # get current state of moves in the statement
        for rec in self:
            if rec.state == 'draft':
                for cr_item in rec.credit_move_line_ids:
                    if cr_item.move_line_id and cr_item.cleared_cc_account:
                        refdict[cr_item.move_line_id.id] = \
                            cr_item.cleared_cc_account

                for dr_item in rec.debit_move_line_ids:
                    if dr_item.move_line_id and dr_item.cleared_cc_account:
                        refdict[dr_item.move_line_id.id] = \
                            dr_item.cleared_cc_account

        # for the statement
        for rec in self:
            # process only if the statement is in draft state
            if rec.state == 'draft':
                ending_date = rec.ending_date
                suppress_ending_date_filter = rec.suppress_ending_date_filter
                vals = self.fetch_data(ending_date,
                                       suppress_ending_date_filter)

                # list of credit lines
                outlist = []
                for cr_item in vals['value']['credit_move_line_ids']:
                    cr_item['cleared_cc_account'] = \
                        refdict and refdict.get(cr_item['move_line_id'],
                                                False) or False
                    cr_item['research_required'] = False

                    item = [0, False, cr_item]
                    outlist.append(item)

                # list of debit lines
                inlist = []
                for dr_item in vals['value']['debit_move_line_ids']:
                    dr_item['cleared_cc_account'] = \
                        refdict and refdict.get(dr_item['move_line_id'],
                                                False) or False
                    dr_item['research_required'] = False

                    item = [0, False, dr_item]
                    inlist.append(item)

                # write it to the record so it is visible on the form
                retval = rec.write({
                    'last_ending_date': vals['value']['last_ending_date'],
                    'starting_balance': vals['value']['starting_balance'],
                    'credit_move_line_ids': outlist,
                    'debit_move_line_ids': inlist})
        return retval

    # Get starting balance for the account
    def get_starting_balance(self, journal_id, account_id, ending_date):
        result = (False, 0.0)
        reslist = []
        statement_obj = self.env['cc.rec.statement']
        domain = [('journal_id', '=', journal_id),
                  ('account_id', '=', account_id),
                  ('state', '=', 'done')]
        statement_ids = statement_obj.search(domain)

        # get all statements for this account in the past
        for statement in statement_ids:
            if statement.ending_date < ending_date:
                reslist.append((statement.ending_date,
                                abs(statement.ending_balance)))

        # get the latest statement value
        if len(reslist):
            reslist = sorted(reslist, key=itemgetter(0))
            result = reslist[len(reslist) - 1]
        return result

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            if not self.journal_id.partner_id:
                raise UserError(_(
                    'Please define the credit card company on the selected '
                    'journal (%s).' % self.journal_id.name))
            self.account_id = \
                self.journal_id.partner_id.property_account_payable_id

    @api.multi
    def fetch_data(self, ending_date, suppress_ending_date_filter):

        aml = self.env['account.move.line']
        sline = self.env['cc.rec.statement.line']
        val = {'value': {'credit_move_line_ids': [],
                         'debit_move_line_ids': []}}

        for rec in self:
            journal_id = rec.journal_id.id
            account_id = rec.account_id.id

            if journal_id and account_id:
                line_ids = sline.search([('statement_id', '=', rec.id)])
                # Call unlink method to reset and remove existing statement
                # lines and mark reset field values in related move lines
                line_ids.unlink()

                # Apply filter on move lines to allow
                # 1. credit and debit side journal items in posted state of
                #    the selected GL account
                # 2. Journal items which are not cleared in previous credit
                #    card statements
                # 3. Date less than or equal to ending date provided the
                #    'Suppress Ending Date Filter' is not checkec
                domain = [('account_id', '=', account_id),
                          ('move_id.state', '=', 'posted'),
                          ('cleared_cc_account', '=', False)]
                if not suppress_ending_date_filter:
                    domain += [('date', '<=', ending_date)]
                line_ids = aml.search(domain)

                for line in line_ids:
                    amount_currency = \
                        (line.amount_currency < 0) and \
                        (-1 * line.amount_currency) or \
                        line.amount_currency

                    # Get partner for the original transaction
                    counterpart_lines = \
                        line.move_id.line_ids.filtered(
                            lambda ids:
                            ids.account_id.id ==
                            ids.journal_id.default_debit_account_id.id)
                    if len(counterpart_lines) >= 2:
                        partner_id = counterpart_lines[1].partner_id
                    else:
                        partner_id = line.partner_id

                    res = {
                        'ref': line.ref,
                        'date': line.date,
                        'partner_id': partner_id.id,
                        'currency_id': line.currency_id.id,
                        'amount': line.credit or line.debit,
                        'amountcur': amount_currency,
                        'name': line.name,
                        'move_line_id': line.id,
                        'type': line.credit and 'cr' or 'dr',
                        'from_filter': True
                    }
                    if res['type'] == 'cr':
                        val['value']['credit_move_line_ids'].append(res)
                    else:
                        val['value']['debit_move_line_ids'].append(res)

                # Look for previous statement for the account to pull ending
                # balance as starting balance
                prev_stmt = self.get_starting_balance(
                    journal_id, account_id, ending_date)
                val['value']['last_ending_date'] = prev_stmt[0]
                val['value']['starting_balance'] = prev_stmt[1]
                val['value']['journal_id'] = journal_id
                val['value']['account_id'] = account_id
        return val

    @api.onchange('suppress_ending_date_filter', 'ending_date')
    def onchange_suppress_date(self):
        return self.fetch_data(self.ending_date,
                               self.suppress_ending_date_filter)

    name = fields.Char(
        'Name', required=True, states={'done': [('readonly', True)]},
        help="This is a unique name identifying the statement "
             "(e.g. Credit Card X January 2012).")
    account_id = fields.Many2one(
        'account.account', string='Account',
        states={'done': [('readonly', True)]},
        domain="[('company_id', '=', company_id), ('type', '!=', 'view')]",
        help="The Credit Card Payable Account that is being reconciled.")
    ending_date = fields.Date(
        'Statement Date', required=True,
        states={'done': [('readonly', True)]},
        default=lambda *a: time.strftime('%Y-%m-%d'),
        help="Statement Date")
    last_ending_date = fields.Date(
        string='Last Statement Date',
        help="The date of the previous credit card statement.")
    starting_balance = fields.Float(
        string='Starting Balance (b/fwd)',
        required=True, digits=dp.get_precision('Account'),
        help="Starting Balance for the current credit card statement.",
        states={'done': [('readonly', True)]})
    ending_balance = fields.Float(
        string='Statement Balance (due)', required=True,
        digits=dp.get_precision('Account'), help="Statement balance (due)",
        states={'done': [('readonly', True)]})
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.user.company_id,
        help="The Company the credit card belongs to")
    notes = fields.Text('Notes')
    verified_date = fields.Date(
        'Verified Date', states={'done': [('readonly', True)]},
        help="Date when the credit card statement was verified.")
    verified_by_user_id = fields.Many2one(
        'res.users', string='Verified By',
        states={'done': [('readonly', True)]},
        help="Entered automatically by the “last user” who saved it. "
             "System generated.")
    credit_move_line_ids = fields.One2many(
        'cc.rec.statement.line', 'statement_id', string='Credits',
        domain=[('type', '=', 'cr')], context={'default_type': 'cr'},
        states={'done': [('readonly', True)]})
    debit_move_line_ids = fields.One2many(
        'cc.rec.statement.line', 'statement_id', string='Debits',
        domain=[('type', '=', 'dr')], context={'default_type': 'dr'},
        states={'done': [('readonly', True)]})
    cleared_balance = fields.Float(
        compute='_compute_balance', string='Cleared Total',
        digits=dp.get_precision('Account'),
        help="Total cleared amount")
    cleared_balance_cur = fields.Float(
        compute='_compute_balance', string='Cleared Total(Cur)',
        digits=dp.get_precision('Account'),
        help="Cleared Total (Cur)")
    difference = fields.Float(
        compute='_compute_balance', string='Difference',
        digits=dp.get_precision('Account'),
        help="(Statement Balance – Cleared Total)")
    difference_cur = fields.Float(
        compute='_compute_balance', string='Difference (Cur)',
        digits=dp.get_precision('Account'),
        help="(Statement Balance – Cleared Total.)")
    uncleared_balance = fields.Float(
        compute='_compute_balance', string='Uncleared Total',
        digits=dp.get_precision('Account'), help="Total Uncleared")
    uncleared_balance_cur = fields.Float(
        compute='_compute_balance', string='Uncleared Total (Cur)',
        digits=dp.get_precision('Account'), help="Total Uncleared (Cur)")
    sum_of_debits = fields.Float(
        compute='_compute_balance', string='Cleared Payments/Credits',
        digits=dp.get_precision('Account'),
        help="Cleared Credit Card Payments, credits")
    sum_of_debits_cur = fields.Float(
        compute='_compute_balance', string='Cleared Payments (Cur)',
        digits=dp.get_precision('Account'),
        help="Cleared Credit Card Payments, Credits (Cur)")
    sum_of_debits_lines = fields.Float(
        compute='_compute_balance',
        string='Number of cleared payments/credits',
        help="Credit Card Payments/Credits # of Items")
    sum_of_credits = fields.Float(
        compute='_compute_balance', string='Cleared Charges',
        digits=dp.get_precision('Account'),
        help="Cleared Credit Card Charges, Fees, Interest and Penalties")
    sum_of_credits_cur = fields.Float(
        compute='_compute_balance', string='Cleared Charges (Cur)',
        digits=dp.get_precision('Account'),
        help="Credit Card Charges, Fees, Interest and Penalties (Cur)")
    sum_of_credits_lines = fields.Float(
        compute='_compute_balance', string='Number of cleared charges',
        help="Credit Card Charges, Fees, Interest and Penalties # of Items")
    sum_of_udebits = fields.Float(
        compute='_compute_balance', string='Uncleared Payments/Credits',
        digits=dp.get_precision('Account'),
        help="Uncleared Credit Card Payments, credits")
    sum_of_udebits_cur = fields.Float(
        compute='_compute_balance', string='Uncleared Payments/Credits (Cur)',
        digits=dp.get_precision('Account'),
        help="Uncleared Credit Card Payments, credits (Cur)")
    sum_of_udebits_lines = fields.Float(
        compute='_compute_balance',
        string='Number of cleared payments/credits',
        help="Credit Card Payments/Credits # of Items")
    sum_of_ucredits = fields.Float(
        compute='_compute_balance', string='Uncleared Charges',
        digits=dp.get_precision('Account'),
        help="Uncleared Credit Card Charges, Fees, Interest and Penalties")
    sum_of_ucredits_cur = fields.Float(
        compute='_compute_balance', string='Uncleared Charges (Cur)',
        digits=dp.get_precision('Account'),
        help="Uncleared Credit Card Charges, Fees, Interest and Penalties "
             "(Cur)")
    sum_of_ucredits_lines = fields.Float(
        compute='_compute_balance', string='Number of uncleared charges',
        help="Credit Card Charges, Fees, Interest and Penalties # of Items")
    suppress_ending_date_filter = fields.Boolean(
        'Show all charges, credits and payments',
        help="If this is checked then the Statement End Date filter on the "
             "transactions below will not occur. "
             "All transactions would come over.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_be_reviewed', 'Ready for Review'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], 'State', index=True, readonly=True, default='draft')
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        states={'done': [('readonly', True)]},
        domain="[('support_creditcard_transactions', '=', True)]")

    _sql_constraints = [
        ('name_company_uniq',
         'unique (name, company_id, account_id)',
         'The name of the statement must be unique per company and G/L'
         ' account!')]

    @api.multi
    def _compute_balance(self):
        """Computed as following:
        A) Credit card payments/credits Amount:
             Total SUM of Amts of lines with Cleared = True
           Credit card payments/credits # of Items:
             Total of number of lines with Cleared = True
        B) Credit card charges, interest and penalties:
           Credit card charges, interest and penalties # of Items:
           Cleared Balance (Total Sum of the Deposit Amount Cleared (A)
                          – Total Sum of Checks Amount Cleared (B))
           Difference = (Statement Balance - cleared balance = should be zero.
        """
        res = {}
        account_precision = self.env['decimal.precision']. \
            precision_get('Account')
        for statement in self:
            res[statement.id] = {
                'sum_of_credits': 0.0,
                'sum_of_debits': 0.0,
                'sum_of_credits_cur': 0.0,
                'sum_of_debits_cur': 0.0,
                'sum_of_ucredits': 0.0,
                'sum_of_udebits': 0.0,
                'sum_of_ucredits_cur': 0.0,
                'sum_of_udebits_cur': 0.0,
                'cleared_balance': 0.0,
                'cleared_balance_cur': 0.0,
                'uncleared_balance': 0.0,
                'uncleared_balance_cur': 0.0,
                'difference': 0.0,
                'difference_cur': 0.0,
                'sum_of_credits_lines': 0.0,
                'sum_of_debits_lines': 0.0,
                'sum_of_ucredits_lines': 0.0,
                'sum_of_udebits_lines': 0.0
            }
            for line in statement.credit_move_line_ids:
                statement.sum_of_credits += \
                    line.cleared_cc_account and \
                    round(line.amount, account_precision) or 0.0
                statement.sum_of_credits_cur += \
                    line.cleared_cc_account and \
                    round(line.amountcur, account_precision) or 0.0
                statement.sum_of_credits_lines += \
                    line.cleared_cc_account and 1.0 or 0.0
                statement.sum_of_ucredits += \
                    (not line.cleared_cc_account) and \
                    round(line.amount, account_precision) or 0.0
                statement.sum_of_ucredits_cur += \
                    (not line.cleared_cc_account) and \
                    round(line.amountcur, account_precision) or 0.0
                statement.sum_of_ucredits_lines += \
                    (not line.cleared_cc_account) and 1.0 or 0.0
            for line in statement.debit_move_line_ids:
                statement.sum_of_debits += \
                    line.cleared_cc_account and \
                    round(line.amount, account_precision) or 0.0
                statement.sum_of_debits_cur += \
                    line.cleared_cc_account and \
                    round(line.amountcur, account_precision) or 0.0
                statement.sum_of_debits_lines += \
                    line.cleared_cc_account and 1.0 or 0.0
                statement.sum_of_udebits += \
                    (not line.cleared_cc_account) and \
                    round(line.amount, account_precision) or 0.0
                statement.sum_of_udebits_cur += \
                    (not line.cleared_cc_account) and \
                    round(line.amountcur, account_precision) or 0.0
                statement.sum_of_udebits_lines += \
                    (not line.cleared_cc_account) and 1.0 or 0.0

            statement.cleared_balance = \
                abs(round(statement.sum_of_debits -
                          statement.sum_of_credits, account_precision))
            statement.cleared_balance_cur = \
                abs(round(statement.sum_of_debits_cur -
                          statement.sum_of_credits_cur, account_precision))
            statement.uncleared_balance = \
                abs(round(statement.sum_of_udebits -
                          statement.sum_of_ucredits, account_precision))
            statement.uncleared_balance_cur = \
                abs(round(statement.sum_of_udebits_cur -
                          statement.sum_of_ucredits_cur, account_precision))
            statement.difference = \
                round((abs(statement.starting_balance -
                           statement.ending_balance) -
                       statement.cleared_balance), account_precision)
            statement.difference_cur = \
                round((abs(statement.starting_balance -
                           statement.ending_balance) -
                       statement.cleared_balance_cur), account_precision)
