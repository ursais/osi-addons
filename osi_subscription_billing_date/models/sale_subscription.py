# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models
import calendar
from dateutil.relativedelta import relativedelta


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
        adb = self.partner_id.authoritative_bill_date
        if not adb or not self.recurring_next_date:
            return values

        # Find billing date, according to current customer billing day
        invoicing_date = self.recurring_next_date
        expected_date = date_set_day(invoicing_date, adb)
        # If billing date not the current one, prorate current invoice
        if expected_date != invoicing_date:
            # find the base date to increment, for the next invoicing date
            # and set as next date to be incremented after invoice generation
            if expected_date < invoicing_date:
                base_date = expected_date
            else:
                base_date = self._get_add_periods(expected_date, -1)
            self.recurring_next_date = base_date
            # Prorate the invoice line
            period_to = self._get_add_periods(base_date) - DAY
            days, ratio = self._prorate_compute_ratio(
                date_from=invoicing_date,
                period_from=base_date,
                period_to=period_to)
            for a, b, line in values.get('invoice_line_ids', []):
                line['quantity'] *= ratio
                line['name'] += " (%d days)" % days
        return values
