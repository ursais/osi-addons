# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
from odoo import api, fields, models, _
from odoo.tools import format_date


DAY = datetime.timedelta(days=1)  # one day, to add to dates


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

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
            values['name'] += " (%d days)" % days
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
        invoice = self._prepare_invoice_data()
        invoice['type'] = inv_type
        # Prepare line
        fiscal_position = self.env['account.fiscal.position'].browse(
            invoice['fiscal_position_id'])
        bill_info = None
        line_values = []
        for line in lines:
            bill_info = line._prorate_calc_periods(date_from, date_to)
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
            date_from=None, date_to=None, inv_type='out_invoice'):
        """
        Creates a new Invoice or Credit Note with the prorated amount to bill
        """
        self.ensure_one()
        values = self._prorate_prepare_invoice(
            lines, date_from, date_to, inv_type)
        new_invoice = self.env['account.invoice'].create(values)
        return new_invoice

    def set_close(self):
        res = super().set_close()
        today = fields.Date.today()
        for subscription in self:
            lines = self.recurring_invoice_line_ids
            subscription._prorate_create_invoice(
                lines, date_to=today, inv_type='out_refund')
        return res


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    start_date = fields.Date()

    def _prorate_calc_periods(self, date_from=None, date_to=None,
                              period_from=None, period_to=None):
        """
        Calculate the last invoice billing period,
        and the billing period to consider for prorating.

        Returns a dict with the calculated values.
        """
        subscription = self.analytic_account_id
        line_start_date = self and self.start_date
        # Period of the last invoice
        period_from = (
            period_from or
            (subscription and subscription.recurring_last_date) or
            (subscription and subscription.date_start))
        period_to = (
            period_to or
            (subscription and subscription.date) or  # End Date
            (subscription and subscription.recurring_next_date - DAY))
        period_delta = period_to - period_from + DAY
        # Period to prorate
        if date_from:
            sign = +1
            bill_from = date_from
            bill_to = date_to or period_to
        else:
            sign = -1
            bill_from = (date_to or line_start_date or period_from) + DAY
            bill_to = period_to
        bill_from = max(bill_from, period_from)
        bill_to = min(bill_to, period_to)
        bill_delta = bill_to - bill_from + DAY
        bill_days = bill_delta.days * sign
        return {
            'period_from': period_from,
            'period_to': period_to,
            'period_days': period_delta.days,
            'bill_from': bill_from,
            'bill_to': bill_to,
            'bill_days': bill_days,
            'ratio': float(bill_days) / period_delta.days,
        }

    @api.model
    def create(self, vals):
        """ Adding a new line creates an immediate prorated invoice for it """
        line = super().create(vals)
        subscription = line.analytic_account_id
        is_in_progress = subscription.stage_id.in_progress
        has_recurring_last_date = bool(subscription.recurring_last_date)
        if is_in_progress and has_recurring_last_date:
            start_date = fields.Date.context_today(self)
            subscription._prorate_create_invoice(
                line, date_from=start_date)
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
            has_recurring_last_date = bool(subscription.recurring_last_date)
            if is_in_progress and has_recurring_last_date:
                end_date = fields.Date.context_today(self)
                subscription._prorate_create_invoice(
                    line, date_to=end_date, inv_type='out_refund')
        return super().unlink()
