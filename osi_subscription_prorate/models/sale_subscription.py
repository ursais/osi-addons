# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
from odoo import api, fields, models, _
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta

DAY = datetime.timedelta(days=1)  # one day, to add to dates


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def _get_invoicing_period(self):
        """ Returns a relativedelta for invoicing time period """
        self.ensure_one()
        periods = {
            'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        invoicing_period = relativedelta(
            **{periods[self.recurring_rule_type]: self.recurring_interval})
        return invoicing_period

    def _prorate_calc_periods(self, date_from=None, date_to=None):
        """
        Calculate the last invoice billing period,
        and the billing period to consider for prorating.

        End dates used in the computations
        are expected to be the day after the period end.

        Returns a dict with the calculated values.

        - period_from and period_to: to use for variable consumption in previous period
        - bill_from, bill_to: to use for the fixed term invoicing
        """
        self.ensure_one()
        # Computation is done before the invoice is created
        # so the invoice date will be the recurring next date.
        this_invoice_date = date_from or self.recurring_next_date
        # Period of the last invoice, to use for variable invoicing
        variable_period_from = self.recurring_last_date or self.date_start
        variable_period_to = this_invoice_date
        # Full period to use as reference for the prorating
        bill_period_from = self.recurring_next_date
        bill_period_to = self.recurring_next_date + self._get_invoicing_period()
        bill_period_days = (bill_period_to - bill_period_from).days
        # Period to prorate
        if date_to and not date_from:
            # End of a service in the middle of the billing period
            # Reverse the already billed period
            bill_from = bill_period_from
            bill_to = date_to
            bill_days = -(bill_to - bill_from).days
        else:
            # Start of a service in the middle of the billing period
            # Invoice the period up to the next billing date (or end of service)
            bill_from = date_from
            bill_to = (date_to + DAY) if date_to else bill_period_to
            bill_days = +(bill_to - bill_from).days
        bill_ratio = bill_days / bill_period_days if bill_period_days else 1
        return {
            # Variable invoicing during previous period
            'period_from': variable_period_from,
            'period_to': variable_period_to - DAY,
            # Fixed service
            'bill_from': bill_from,
            'bill_to': bill_to - DAY,
            'bill_days': bill_days,
            'ratio': bill_ratio,
        }

    def _prorate_invoice_line(self, line, fiscal_position, ratio, days):
        """
        Prepares the values for a prorated invoice line.
        Only consider lines for recurring products, ignore lines
        for other products and services.
        Ratio and Days can both be positive or negative.
        """
        if line.product_id.recurring_invoice:
            values = self._prepare_invoice_line(line, fiscal_position)
            values['quantity'] *= ratio
            if days < 0:
                days = days * -1
            values['name'] += " (%d days)" % days
            values['start_date'] = line.start_date
            return values

    def _prorate_prepare_invoice(
            self, lines,
            date_from=None, date_to=None, inv_type='out_invoice'):
        """
        Prepares the values for a prorated invoice
        """
        self.ensure_one()
        # Prepare Header, using Customer's language
        self = self.with_context(lang=self.partner_id.lang)
        invoice = self._prepare_invoice()
        invoice['type'] = inv_type
        # Prepare line
        fiscal_position = self.env['account.fiscal.position'].browse(
            invoice['fiscal_position_id'])
        bill_info = None
        line_values = []
        bill_info = self._prorate_calc_periods(date_from, date_to)
        for line in lines:
            values = self._prorate_invoice_line(
                line,
                fiscal_position,
                bill_info['ratio'],
                bill_info['bill_days'])
            if values:
                line_values.append(values)
        # Add to invoice values
        invoice['invoice_line_ids'] = [
            (0, 0, value) for value in line_values]
        if bill_info:
            invoice['comment'] = (
                _('This invoice covers the following period: %s - %s')
                % (format_date(self.env, bill_info['bill_from']),
                   format_date(self.env, bill_info['bill_to']))
            )
        return invoice

    def _prorate_create_invoice(
            self, lines,
            date_from=None, date_to=None,
            inv_type='out_invoice',
            increment_next_date=True):
        """
        Creates a new Invoice or Credit Note with the prorated amount to bill
        """
        self.ensure_one()
        values = self._prorate_prepare_invoice(
            lines, date_from, date_to, inv_type)
        new_invoice = self.env['account.invoice'].create(values)
        if increment_next_date:
            self.recurring_next_date += self._get_invoicing_period()
        return new_invoice

    def set_close(self):
        res = super().set_close()
        today = fields.Date.today()
        for subscription in self:
            lines = self.recurring_invoice_line_ids
            inv = subscription._prorate_create_invoice(
                lines, date_to=today, inv_type='out_refund')
            for line_id in inv.invoice_line_ids:
                non_use_days = self.recurring_next_date - today
                # total_days = self.recurring_next_date - self.recurring_last_date
                prev_date = self.recurring_next_date - relativedelta(months=1)
                total_days = self.recurring_next_date - prev_date
                line_id.quantity = non_use_days.days/total_days.days
                desc = line_id.name
                new_desc = desc.split(')', 1)[0]
                line_id.name = new_desc + ") (%d days)" % non_use_days.days
        return res

    @api.multi
    def set_in_progress(self):
        # TODO: redundant? call _prorate_create_invoice with a date_start
        self.stage_id = self.env.ref(
            'sale_subscription.sale_subscription_stage_in_progress')
        is_in_progress = self.stage_id.in_progress
        today = fields.Date.today()
        if is_in_progress and self.recurring_invoice_line_ids:
            lines = self.recurring_invoice_line_ids
            # Set ABD to today
            if not self.partner_id.authoritative_bill_date:
                day = str(today.day)
                # ABD between '1'-'30'
                if day == '31':
                    day = '1'
                self.partner_id.write({'authoritative_bill_date': day})
            # Set Next Bill Date
            next_date = today
            if int(self.partner_id.authoritative_bill_date) <= today.day:
                next_date = next_date + relativedelta(months=1)
            next_date = next_date.replace(
                day=int(self.partner_id.authoritative_bill_date))
            prev_date = next_date - relativedelta(months=1)
            self.recurring_next_date = next_date
            if not self.recurring_last_date:
                self.recurring_last_date = prev_date
            inv = self._prorate_create_invoice(
                lines, date_to=today, inv_type='out_invoice')
            self.recurring_last_date = today
            total_days = prev_date - next_date
            use_days = today - next_date
            for line_id in inv.invoice_line_ids:
                line_id.write({'quantity': use_days.days/total_days.days})
                desc = line_id.name
                new_desc = desc.split(')', 1)[0]
                use_days = use_days.days * -1
                new_desc = new_desc + ") (%d days)" % use_days
                line_id.write({'name': new_desc})
            for sub_line_id in self.recurring_invoice_line_ids:
                if not sub_line_id.start_date:
                    sub_line_id.write({'start_date': today})


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    start_date = fields.Date()

    @api.model
    def create(self, vals):
        """ Adding a new line creates an immediate prorated invoice for it """
        line = super().create(vals)
        subscription = line.analytic_account_id
        if subscription.stage_id.in_progress:
            start_date = fields.Date.context_today(self)
            subscription._prorate_create_invoice(
                line, date_from=start_date, increment_next_date=True)
            line.start_date = start_date
        return line

    def unlink(self):
        """
        When a Subscription Line is deleted,
        create Credit Note for the unused service days.
        """
        for line in self:
            subscription = line.analytic_account_id
            is_in_progress = subscription.stage_id.in_progress
            if is_in_progress:
                end_date = fields.Date.context_today(self) - relativedelta(days=1)
                subscription._prorate_create_invoice(
                    line, date_to=end_date, inv_type='out_refund',
                    increment_next_date=False)
        return super().unlink()
