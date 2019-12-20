# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import datetime
from odoo import api, fields, models, _
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def prorate_note_line(self, account_invoice, option_line, ratio):
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        inv_line_obj = self.env['account.invoice.line']
        values = {
            'invoice_id': account_invoice.id,
            'product_id': option_line.product_id.id,
            'subscription_id': self.id,
            'quantity': option_line.quantity * ratio,
            'uom_id': option_line.uom_id.id,
            'price_unit': self.pricelist_id.with_context({'uom': option_line.uom_id.id}).get_product_price(option_line.product_id, 1, False),
            'name': option_line.name,
            'account_id': account_invoice.partner_id.property_account_receivable_id.id,
            'account_analytic_id': self.analytic_account_id.id,
        }
        return inv_line_obj.create(values)

    @api.multi
    def create_prorated_note(self, ratio, days_diff):
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
        invoice_obj = self.env['account.invoice']
        team = self.env['crm.team']._get_default_team_id(user_id=self.user_id.id)
        new_inv_vals = {
            'partner_id': self.partner_id.id,
            'team_id': team and team.id,
            'fiscal_position_id': fpos_id,
            'origin': self.code,
            'type': 'out_refund',
            'name': 'Credit For ' + str(days_diff) + ' Unused Days'
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.partner_id.property_payment_term_id:
            new_inv_vals['payment_term_id'] = self.partner_id.property_payment_term_id.id
        inv = invoice_obj.create(new_inv_vals)
        for line_id in self.recurring_invoice_line_ids:
            self.prorate_note_line(inv, line_id, ratio)
        inv.action_invoice_open()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.invoice",
            "views": [[False, "form"]],
            "res_id": inv.id,
        }

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        res = super().onchange_stage_id()
        if self.stage_id.name == 'Closed':
            # Count the number of days each line has been active this billing cycle
            next_date = self.recurring_next_date
            today = date.today()
            billing_cycle = calendar.monthrange(today.year, today.month)[1]
            delta = (next_date - today)
            days_diff = delta.days
            ratio = float(days_diff/billing_cycle)
            self.create_prorated_note(ratio, days_diff)
        if self.stage_id.name == 'In Progress':
            # Generate Invoice
            fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
            invoice_obj = self.env['account.invoice']
            team = self.env['crm.team']._get_default_team_id(user_id=self.user_id.id)
            new_inv_vals = {
                'partner_id': self.partner_id.id,
                'team_id': team and team.id,
                'fiscal_position_id': fpos_id,
                'origin': self.code,
                'type': 'out_invoice',
            }
            if self.partner_id.property_payment_term_id:
                new_inv_vals['payment_term_id'] = self.partner_id.property_payment_term_id.id
            inv = invoice_obj.create(new_inv_vals)
            for line_id in self.recurring_invoice_line_ids:
                inv_line_obj = self.env['account.invoice.line']
                values = {
                    'invoice_id': inv.id,
                    'product_id': line_id.product_id.id,
                    'subscription_id': self.id,
                    'quantity': line_id.quantity,
                    'uom_id': line_id.uom_id.id,
                    'price_unit': self.pricelist_id.with_context({'uom': line_id.uom_id.id}).get_product_price(line_id.product_id, 1, False),
                    'name': line_id.name,
                    'account_id': inv.partner_id.property_account_receivable_id.id,
                    'account_analytic_id': self.analytic_account_id.id,
                    'last_invoice_date': date.today()
                }
                inv_line_obj.create(values)
            inv.action_invoice_open()
        return res

    def prorate_abd_invoice_line(self, account_invoice, option_line, ratio):
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        inv_line_obj = self.env['account.invoice.line']
        values = {
            'invoice_id': account_invoice.id,
            'product_id': option_line.product_id.id,
            'subscription_id': self.id,
            'quantity': option_line.quantity * ratio,
            'uom_id': option_line.uom_id.id,
            'price_unit': self.pricelist_id.with_context({'uom': option_line.uom_id.id}).get_product_price(option_line.product_id, 1, False),
            'name': option_line.name,
            'account_id': account_invoice.partner_id.property_account_receivable_id.id,
            'account_analytic_id': self.analytic_account_id.id,
        }
        return inv_line_obj.create(values)

    @api.multi
    def create_prorated_abd_invoice(self, ratio, days_diff):
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
        invoice_obj = self.env['account.invoice']
        team = self.env['crm.team']._get_default_team_id(user_id=self.user_id.id)
        new_inv_vals = {
            'partner_id': self.partner_id.id,
            'team_id': team and team.id,
            'fiscal_position_id': fpos_id,
            'origin': self.code,
            'type': 'out_invoice',
            'name': 'Invoiced For ' + str(days_diff) + ' Days'
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.partner_id.property_payment_term_id:
            new_inv_vals['payment_term_id'] = self.partner_id.property_payment_term_id.id
        inv = invoice_obj.create(new_inv_vals)
        for line in self.recurring_invoice_line_ids:
            self.prorate_abd_invoice_line(inv, line, ratio)
            # Update Last Invoice Date when generating invoices
            line.last_invoice_date = date.today()
        inv.action_invoice_open()

    def wizard_change_recurring_next_date(self, next_month):
        # Save the previous Next Bill Date
        old_date = self.recurring_next_date
        # Change to the new New Bill Date
        res = super().wizard_change_recurring_next_date(next_month)
        # Bill the number of days between the two dates
        new_date = self.recurring_next_date
        billing_cycle = calendar.monthrange(old_date.year, old_date.month)[1]
        delta = (new_date - old_date)
        days_diff = delta.days
        ratio = float(days_diff/billing_cycle)
        self.create_prorated_abd_invoice(ratio, days_diff)
        return res

    def recurring_invoice(self):
        res = super().recurring_invoice()
        for line_id in self.recurring_invoice_line_ids:
            line_id.last_invoice_date = date.today()
        return res

    def write(self, vals):
        if vals.get('stage_id', False):
            if self.stage_id.name == 'Closed':
                raise UserError(_('Closed Subscriptions Cannot Be Reopened'))
        return super().write(vals)


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    @api.model
    def create(self, vals):
        """ Adding a new line creates an immediate prorated invoice for it """
        res = super().create(vals)
        if res.analytic_account_id.stage_id.name == 'In Progress':
            # They are going to be billed from now until Next Bill Date.
            next_date = res.analytic_account_id.recurring_next_date
            today = date.today()
            billing_cycle = calendar.monthrange(today.year, today.month)[1]
            # TODO we want to be able to select the start date
            delta = (next_date - today)
            days_diff = delta.days
            ratio = float(days_diff/billing_cycle)
            # TODO single point for the Invoice creation
            self.create_new_service_invoice(res.analytic_account_id, ratio, days_diff, res)
            # Update Last Invoice Date when generating invoices
            res.last_invoice_date = date.today()
        return res

    def prorate_new_service_invoice_line(self, subscription_id, account_invoice, ratio, line_id):
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        inv_line_obj = self.env['account.invoice.line']
        values = {
            'invoice_id': account_invoice.id,
            'product_id': line_id.product_id.id,
            'subscription_id': subscription_id.id,
            'quantity': line_id.quantity * ratio,
            'uom_id': line_id.uom_id.id,
            'price_unit': subscription_id.pricelist_id.with_context({'uom': line_id.uom_id.id}).get_product_price(line_id.product_id, 1, False),
            'name': line_id.name,
            'account_id': account_invoice.partner_id.property_account_receivable_id.id,
            'account_analytic_id': subscription_id.analytic_account_id.id,
        }
        return inv_line_obj.create(values)

    @api.multi
    def create_new_service_invoice(self, subscription_id, ratio, days_diff, line_id):
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(subscription_id.partner_id.id)
        invoice_obj = self.env['account.invoice']
        team = self.env['crm.team']._get_default_team_id(user_id=self.env.user.id)
        new_inv_vals = {
            'partner_id': subscription_id.partner_id.id,
            'team_id': team and team.id,
            'fiscal_position_id': fpos_id,
            'origin': subscription_id.code,
            'type': 'out_invoice',
            'name': 'Invoiced For ' + str(days_diff) + ' Days'
        }
        # we don't override the default if no payment terms has been set on the customer
        if subscription_id.partner_id.property_payment_term_id:
            new_inv_vals['payment_term_id'] = subscription_id.partner_id.property_payment_term_id.id
        inv = invoice_obj.create(new_inv_vals)
        self.prorate_new_service_invoice_line(subscription_id, inv, ratio, line_id)
        inv.action_invoice_open()

    @api.multi
    def unlink(self):
        for line_id in self:
            if line_id.analytic_account_id.stage_id.name == 'In Progress':
                # Count the number of days this line has been active this billing cycle
                next_date = line_id.analytic_account_id.recurring_next_date
                today = date.today()
                billing_cycle = calendar.monthrange(today.year, today.month)[1]
                delta = (next_date - today)
                days_diff = delta.days
                ratio = float(days_diff/billing_cycle)
                self.create_remove_service_note(line_id.analytic_account_id, ratio, days_diff, line_id)
        return super().unlink()

    def remove_service_note_line(self, subscription_id, account_invoice, ratio, line_id):
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        inv_line_obj = self.env['account.invoice.line']
        values = {
            'invoice_id': account_invoice.id,
            'product_id': line_id.product_id.id,
            'subscription_id': subscription_id.id,
            'quantity': line_id.quantity * ratio,
            'uom_id': line_id.uom_id.id,
            'price_unit': subscription_id.pricelist_id.with_context({'uom': line_id.uom_id.id}).get_product_price(line_id.product_id, 1, False),
            'name': line_id.name,
            'account_id': account_invoice.partner_id.property_account_receivable_id.id,
            'account_analytic_id': subscription_id.analytic_account_id.id,
        }
        return inv_line_obj.create(values)

    @api.multi
    def create_remove_service_note(self, subscription_id, ratio, days_diff, line_id):
        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(subscription_id.partner_id.id)
        invoice_obj = self.env['account.invoice']
        team = self.env['crm.team']._get_default_team_id(user_id=self.env.user.id)
        new_inv_vals = {
            'partner_id': subscription_id.partner_id.id,
            'team_id': team and team.id,
            'fiscal_position_id': fpos_id,
            'origin': subscription_id.code,
            'type': 'out_refund',
            'name': 'Credit For ' + str(days_diff) + ' Days'
        }
        # we don't override the default if no payment terms has been set on the customer
        if subscription_id.partner_id.property_payment_term_id:
            new_inv_vals['payment_term_id'] = subscription_id.partner_id.property_payment_term_id.id
        inv = invoice_obj.create(new_inv_vals)
        self.remove_service_note_line(subscription_id, inv, ratio, line_id)
        inv.action_invoice_open()
