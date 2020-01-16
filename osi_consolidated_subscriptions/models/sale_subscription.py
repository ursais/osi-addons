# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models
from datetime import datetime
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def wizard_change_recurring_next_date(self, next_month):
        day_next = self.partner_id.authoritative_bill_date
        # old_date = self.recurring_next_date
        if next_month:
            self.increment_period()
        if day_next == 'eom' or (self.recurring_next_date.month == '2' and day_next in ['29', '30']):
            day = calendar.monthrange(self.recurring_next_date.year,self.recurring_next_date.month)[1]
            month = self.recurring_next_date.month
            year = self.recurring_next_date.year
            final = datetime(year, month, day).date()
            self.recurring_next_date = final
        else:
            day = int(day_next)
            month = self.recurring_next_date.month
            year = self.recurring_next_date.year
            final = datetime(year, month, day).date()
            self.recurring_next_date = final


    @api.onchange('stage_id')
    def onchange_stage_id(self):
        super().onchange_stage_id()
        if self.stage_id.name == 'In Progress':
            if self.recurring_next_date == date.today():
                periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
                invoicing_period = relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
                recurring_next_invoice = self.date_start + invoicing_period
                self.recurring_next_date = recurring_next_invoice
            subscription_ids = self.env['sale.subscription'].search([('partner_id', '=', self.partner_id.id), ('id', '!=', self._origin.id)])

    def recurring_invoice(self):
        res = super().recurring_invoice()
        self.check_abd_change(self.partner_id)
        return res

    def check_abd_change(self, partner_id):
        subscription_ids = self.env['sale.subscription'].search([('partner_id', '=', partner_id.id)])
        today = date.today()
        abd = partner_id.authoritative_bill_date
        if (abd in ['29', '30'] and today.months == '2') or abd == 'eof':
            expected_day = calendar.monthrange(date.today().year,date.today().month)[1]
        else:
            expected_day = int(abd)
        for subscription_id in subscription_ids:
            if subscription_id.recurring_next_date.day != expected_day:
                if expected_day > subscription_id.recurring_next_date.day:
                    subscription_id.wizard_change_recurring_next_date(0)
                else:
                    subscription_id.wizard_change_recurring_next_date(1)
