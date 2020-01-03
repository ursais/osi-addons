# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
from odoo import api, fields, models, _


DAY = datetime.timedelta(days=1)  # one day, to add to dates


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def _prorate_compute_ratio(self, date_from=None, date_to=None,
                               period_from=None, period_to=None):
        """
        Compute the quantity to bill or refund.
        Use date_from to bill, or date_to to refund.

        Returns a signed number of days to bill,
        and a signed ratio to apply.
        """
        self.ensure_one()
        period_from = (
            period_from or
            self.recurring_last_date or
            self.date_start)
        period_to = period_to or (self.recurring_next_date - DAY)
        period_period = period_to - period_from + DAY
        if date_from:
            bill_period = period_to - date_from + DAY
        else:
            bill_period = -(period_to - date_to)
        bill_days = float(bill_period.days)
        ratio = bill_days / period_period.days
        return bill_days, ratio

    def _prorate_invoice_line(self, line, fiscal_position, ratio, days):
        """
        Prepares the values for a prorated invoice line
        """
        values = self._prepare_invoice_line(line, fiscal_position)
        values['quantity'] *= ratio
        values['name'] += " (%d days)" % days
        return values

    def _prorate_invoice(self, lines, date_from=None, date_to=None):
        """
        Prepares the values for a prorated invoice
        """
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        invoice = self._prepare_invoice_data()
        days, ratio = self._prorate_compute_ratio(
            date_from=date_from, date_to=date_to)
        if days < 0:
            invoice['comment'] = _('Credit for %d days') % abs(days)
            invoice['type'] = 'out_refund'
        # Prepare line
        fiscal_position = self.env['account.fiscal.position'].browse(
            invoice['fiscal_position_id'])
        line_values = [
            self._prorate_invoice_line(
                line, fiscal_position, ratio, days)
            for line in lines]
        # Add to invoice values
        invoice['invoice_line_ids'] = [
            (0, 0, value) for value in line_values]
        return invoice

    def _prorate_create_invoice(self, lines, date_from=None, date_to=None):
        """
        Creates a new Invoice or Credit Note with the prorated amount to bill
        """
        self.ensure_one()
        values = self._prorate_invoice(lines, date_from, date_to)
        new_invoice = self.env['account.invoice'].create(values)
        return new_invoice

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        res = super().onchange_stage_id()
        if self.stage_id.name == 'Closed':
            today = fields.Date.today()
            lines = self.recurring_invoice_line_ids
            self._prorate_create_invoice(lines, to_date=today)
        return res

    def set_close(self):
        res = super().set_close()
        today = fields.Date.today()
        for subscription in self:
            lines = self.recurring_invoice_line_ids
            subscription._prorate_create_invoice(lines, date_to=today)
        return res


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    @api.model
    def create(self, vals):
        """ Adding a new line creates an immediate prorated invoice for it """
        line = super().create(vals)
        subscription = line.analytic_account_id
        is_in_progress = subscription.stage_id.in_progress
        has_recurring_last_date = bool(subscription.recurring_last_date)
        if is_in_progress and has_recurring_last_date:
            today = fields.Date.today()
            subscription._prorate_create_invoice(line, date_from=today)
        return line

    @api.multi
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
                today = fields.Date.today()
                subscription._prorate_create_invoice(line, date_to=today)
        return super().unlink()
