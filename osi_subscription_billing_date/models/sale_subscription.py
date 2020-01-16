# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import calendar
from dateutil.relativedelta import relativedelta
from odoo import models, _
from odoo.tools import format_date


DAY = relativedelta(days=1)  # one day, to add to dates


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def _get_add_periods(self, current_date=None, periods=1):
        self.ensure_one()
        current_date = current_date or self.recurring_next_date
        period_map = {
            'daily': 'days',
            'weekly': 'weeks',
            'monthly': 'months',
            'yearly': 'years'}
        period = period_map[self.recurring_rule_type]
        interval = self.recurring_interval * periods
        new_date = current_date + relativedelta(**{period: interval})
        return new_date

    def _prepare_invoice(self):
        """
        Detect if the Billing Day has changed.
        if so, adjust the invoiced quantity to the interrim period
        until the next regular billing date.

        The recurring_next_date is the date we creating the invoice
        for the next period. If the billing day was changed,
        we create a prorated invoice and adjust the next date.

        This happens during the regular _recurring_create_invoice()
        process.

        After it runs, one period will be incremented to the
        next invoice date (recurring_next_date).

        So we also need to set the current "next date" to be one period
        before the next intended invoicing date.
        """
        def date_set_day(my_date, day):
            day = 31 if day == 'eom' else int(day)
            last_day = calendar.monthrange(my_date.year, my_date.month)[1]
            return my_date.replace(day=min(day, last_day))

        values = super()._prepare_invoice()
        # Find billing date, according to current customer billing day
        # If billing date not the current one, prorate current invoice
        adb = self.partner_id.authoritative_bill_date
        current_date = self.recurring_next_date
        add_period = self._get_add_periods
        expected_current_date = add_period(
            date_set_day(
                add_period(current_date, -1), adb))
        if expected_current_date != current_date:
            # Billling day was adjusted
            # Base date is used to simulate a full period and compute ratio
            # find the base date to increment, for the next invoicing date
            # and set as next date to be incremented after invoice generation
            date_from = current_date
            period_from = expected_current_date
            if period_from >= date_from:
                period_from = self._get_add_periods(period_from, -1)
            next_date = self._get_add_periods(period_from)
            period_to = next_date - DAY
            # Prorate the invoice line
            Line = self.env['sale.subscription.line']
            bill_dates = Line._prorate_calc_periods(
                date_from=date_from,
                period_from=period_from,
                period_to=period_to)
            for a, b, line_vals in values.get('invoice_line_ids', []):
                line_vals['quantity'] *= bill_dates['ratio']
                line_vals['name'] += " (%d days)" % bill_dates['bill_days']

            values['comment'] = (
                _('This invoice is a billing period adjustment,'
                  ' and covers the following period: %s - %s')
                % (format_date(self.env, date_from),
                   format_date(self.env, period_to))
            )
            self.recurring_next_date = period_from  # Will be incremented
        return values
