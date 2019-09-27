# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.tools.misc import formatLang, format_date

LINE_FILLER = '*'
INV_LINES_PER_STUB = 8
INV_LINES_PER_PAGE = 31

class ReportPrintCheck(models.Model):
    _inherit = 'account.payment'

    def fill_line(self, amount_str):
        return amount_str and (amount_str+' ').ljust(200, LINE_FILLER) or ''

    def get_pages(self):
        """ Returns the data structure used by the template : a list of dicts
            containing what to print on pages.
        """
        stub_pages = self.make_stub_pages() or [False]
        multi_stub = self.company_id.us_check_multi_stub
        pages = []
        for i, p in enumerate(stub_pages):
            pages.append({
                'sequence_number': self.check_number\
                    if (self.journal_id.check_manual_sequencing and self.check_number != 0)\
                    else False,
                'payment_date': format_date(self.env, self.payment_date),
                'partner_id': self.partner_id,
                'partner_name': self.partner_id.name,
                'partner_street': self.partner_id.street,
                'partner_street2': self.partner_id.street2,
                'partner_city': self.partner_id.city,
                'partner_state': self.partner_id.state_id.code,
                'partner_zip': self.partner_id.zip,
                'partner_country': self.partner_id.country_id.name\
                    if (self.partner_id.country_id != self.company_id.country_id\
                    and self.partner_id.country_id.code == 'US')\
                    else False, #Do not print country on check if payee's country is US and is the same as payer's
                'currency': self.currency_id,
                'state': self.state,
                'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
                'amount_in_word': self.fill_line(self.check_amount_in_words) if i == 0 else 'VOID',
                'memo': self.communication,
                'stub_cropped': not multi_stub and len(self.invoice_ids) > INV_LINES_PER_STUB,
                # If the payment does not reference an invoice, there is no stub line to display
                'stub_lines': p,
            })
        return pages

    def make_stub_pages(self):
        """ The stub is the summary of paid invoices. It may spill on several
            pages, in which case only the check on first page is valid.
            This function returns a list of stub lines per page.
        """
        invoice_ids_list = ''
        if len(self.invoice_ids) == 0:

            # use alternate means to find the associated invoices
            exclude_move_line_id = False
            for item in self.move_line_ids:
                reconcile_id = item.full_reconcile_id
                if reconcile_id:
                    exclude_move_line_id = item.id
                    break

            if reconcile_id:
                move_line_ids = self.env['account.move.line'].search([('full_reconcile_id','=',reconcile_id.id),('id','!=', exclude_move_line_id)])
                move_ids = []
                for item in move_line_ids:
                    move_ids.append(item.move_id.id)
                if len(move_ids):
                    invoice_ids_list = self.env['account.invoice'].search([('move_id', 'in', move_ids)])
            if not len(invoice_ids_list):
                return None
            else:
                invoice_ids =invoice_ids_list
        else:
            invoice_ids = self.invoice_ids

        multi_stub = self.company_id.us_check_multi_stub

        invoices = invoice_ids.sorted(key=lambda r: r.date_due)
        debits = invoices.filtered(lambda r: r.type == 'in_invoice')
        credits = invoices.filtered(lambda r: r.type == 'in_refund')

        # Prepare the stub lines
        if not credits:
            stub_lines = [self.make_stub_line(inv) for inv in invoices]
        else:
            stub_lines = [{'header': True, 'name': "Bills"}]
            stub_lines += [self.make_stub_line(inv) for inv in debits]
            stub_lines += [{'header': True, 'name': "Refunds"}]
            stub_lines += [self.make_stub_line(inv) for inv in credits]

        # Crop the stub lines or split them on multiple pages
        if not multi_stub:
            # If we need to crop the stub, leave place for an ellipsis line
            num_stub_lines = len(stub_lines) > INV_LINES_PER_STUB and INV_LINES_PER_STUB-1 or INV_LINES_PER_STUB
            stub_pages = [stub_lines[:num_stub_lines]]
        else:
            stub_pages = []
            i = 0
            while i < len(stub_lines):
                # Make sure we don't start the credit section at the end of a page
                if len(stub_lines) >= i+INV_LINES_PER_STUB and stub_lines[i+INV_LINES_PER_STUB-1].get('header'):
                    num_stub_lines = INV_LINES_PER_STUB-1 or INV_LINES_PER_STUB
                else:
                    num_stub_lines = INV_LINES_PER_STUB
                stub_pages.append(stub_lines[i:i+num_stub_lines])
                i += num_stub_lines

        return stub_pages

    def make_stub_line(self, invoice):
        """ Return the dict used to display an invoice/refund in the stub
        """

        special = False
        # Find the account.partial.reconcile which are common to the invoice and the payment
        if invoice.type in ['in_invoice', 'out_refund']:
            invoice_sign = 1
            invoice_payment_reconcile = invoice.move_id.line_ids.mapped('matched_debit_ids').filtered(lambda r: r.debit_move_id in self.move_line_ids)

        else:
            invoice_sign = -1
            invoice_payment_reconcile = invoice.move_id.line_ids.mapped('matched_credit_ids').filtered(lambda r: r.credit_move_id in self.move_line_ids)

            if not invoice_payment_reconcile:            
                invoice_payment_reconcile = [l for l in invoice.move_id.line_ids if l.full_reconcile_id][0]
                special = True

        if special:
            amount_paid = invoice_payment_reconcile.debit
            purchase_ref = invoice_payment_reconcile.purchase_ref
            supplier_info = invoice_payment_reconcile.supplier_invoice_number

        else:
            purchase_ref = (invoice_payment_reconcile.debit_move_id.debit and invoice_payment_reconcile.credit_move_id.purchase_ref) or (invoice_payment_reconcile.credit_move_id.credit and invoice_payment_reconcile.debit_move_id.purchase_ref)
            if invoice.type in ['out_refund'] and not purchase_ref:
                purchase_ref = invoice_payment_reconcile.credit_move_id.purchase_ref
            supplier_info = (invoice_payment_reconcile.debit_move_id.debit and invoice_payment_reconcile.credit_move_id.supplier_invoice_number) or (invoice_payment_reconcile.credit_move_id.credit and invoice_payment_reconcile.debit_move_id.supplier_invoice_number)

            if self.currency_id != self.journal_id.company_id.currency_id:
                amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount_currency')))
            else:
                amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount')))

        amount_residual = invoice_sign * invoice.residual

        if isinstance(supplier_info, tuple) or isinstance(supplier_info, list):
            supplier_info = supplier_info[0]

        return {
            'due_date': format_date(self.env, invoice.date_due),
            'inv_date': format_date(self.env, invoice.date_invoice),
            'number': invoice.reference and invoice.number + ' - ' + invoice.reference or invoice.number,
            'amount_total': formatLang(self.env, invoice_sign * invoice.amount_total, currency_obj=invoice.currency_id),
            'amount_residual': formatLang(self.env, amount_residual, currency_obj=invoice.currency_id) if amount_residual*10**4 != 0 else '-',
            'amount_paid': formatLang(self.env, invoice_sign * amount_paid, currency_obj=invoice.currency_id),
            'currency': invoice.currency_id,
            'purchase_ref':  purchase_ref,
            'supplier_info': supplier_info,
        }

    def get_stub_pages(self):
        """ Returns the data structure used by the template : a list of dicts
            containing what to print on pages.
        """
        stub_pages = self.make_check_stub_pages() or [False]
        multi_stub = self.company_id.us_check_multi_stub
        pages = []
        for i, p in enumerate(stub_pages):
            pages.append({
                'seq_number': self.check_number\
                    if (self.check_number != 0) else False,
                'sequence_number': self.check_number\
                    if (self.journal_id.check_manual_sequencing and self.check_number != 0)\
                    else False,
                'payment_date': format_date(self.env, self.payment_date),
                'partner_id': self.partner_id,
                'partner_name': self.partner_id.name,
                'partner_street': self.partner_id.street,
                'partner_street2': self.partner_id.street2,
                'partner_city': self.partner_id.city,
                'partner_state': self.partner_id.state_id.code,
                'partner_zip': self.partner_id.zip,
                'partner_country': self.partner_id.country_id.name\
                    if (self.partner_id.country_id != self.company_id.country_id\
                    and self.partner_id.country_id.code == 'US')\
                    else False, #Do not print country on check if payee's country is US and is the same as payer's
                'currency': self.currency_id,
                'state': self.state,
                'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
                'amount_in_word': self.fill_line(self.check_amount_in_words) if i == 0 else 'VOID',
                'memo': self.communication,
                'stub_cropped': not multi_stub and len(self.invoice_ids) > INV_LINES_PER_PAGE,
                # If the payment does not reference an invoice, there is no stub line to display
                'stub_lines': p,
            })
        return pages

    def make_check_stub_pages(self):
        """ The stub is the summary of paid invoices. It may spill on several
            pages, in which case only the check on first page is valid.
            This function returns a list of stub lines per page.
        """
        invoice_ids_list = ''
        if len(self.invoice_ids) == 0:

            # use alternate means to find the associated invoices
            exclude_move_line_id = False
            for item in self.move_line_ids:
                reconcile_id = item.full_reconcile_id
                if reconcile_id:
                    exclude_move_line_id = item.id
                    break

            if reconcile_id:
                move_line_ids = self.env['account.move.line'].search([('full_reconcile_id','=',reconcile_id.id),('id','!=', exclude_move_line_id)])
                move_ids = []
                for item in move_line_ids:
                    move_ids.append(item.move_id.id)
                if len(move_ids):
                    invoice_ids_list = self.env['account.invoice'].search([('move_id', 'in', move_ids)])
            if not len(invoice_ids_list):
                return None
            else:
                invoice_ids =invoice_ids_list
        else:
            invoice_ids = self.invoice_ids

        multi_stub = self.company_id.us_check_multi_stub

        invoices = invoice_ids.sorted(key=lambda r: r.date_due)
        debits = invoices.filtered(lambda r: r.type == 'in_invoice')
        credits = invoices.filtered(lambda r: r.type == 'in_refund')

        # Prepare the stub lines
        if not credits:
            stub_lines = [self.make_stub_line(inv) for inv in invoices]
        else:
            stub_lines = [{'header': True, 'name': "Bills"}]
            stub_lines += [self.make_stub_line(inv) for inv in debits]
            stub_lines += [{'header': True, 'name': "Refunds"}]
            stub_lines += [self.make_stub_line(inv) for inv in credits]

        # Crop the stub lines or split them on multiple pages
        if not multi_stub:
            # If we need to crop the stub, leave place for an ellipsis line
            num_stub_lines = len(stub_lines) > INV_LINES_PER_PAGE and INV_LINES_PER_PAGE-1 or INV_LINES_PER_PAGE
            stub_pages = [stub_lines[:num_stub_lines]]
        else:
            stub_pages = []
            i = 0
            while i < len(stub_lines):
                # Make sure we don't start the credit section at the end of a page
                if len(stub_lines) >= i+INV_LINES_PER_PAGE and stub_lines[i+INV_LINES_PER_PAGE-1].get('header'):
                    num_stub_lines = INV_LINES_PER_PAGE-1 or INV_LINES_PER_PAGE
                else:
                    num_stub_lines = INV_LINES_PER_PAGE
                stub_pages.append(stub_lines[i:i+num_stub_lines])
                i += num_stub_lines

        return stub_pages
