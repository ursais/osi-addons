# Copyright (C) 2019, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import date, timedelta
from odoo import api, fields, models


class SaleSubscription(models.Model):

    _inherit = 'sale.subscription'

    recurring_last_date = fields.Date()

    def _prepare_invoice_variable_dates(self):
        """
        Variable amounts are billed for the previous period.
        The dates for the previous billing period.
        """
        self.ensure_one()
        start_date = self.recurring_last_date or date(1900, 1, 1)
        end_date = self.recurring_next_date - timedelta(days=1)
        return start_date, end_date

    @api.model
    def _prepare_invoice_variable_name(self, analytic_line):
        """Returns the description to use for the invoice line"""
        self.ensure_one()
        return analytic_line.product_id.display_name

    @api.model
    def _prepare_invoice_analytic_domain(self, start_date, end_date):
        return [
            ('account_id', '=', self.analytic_account_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('amount', '!=', 0.0),
            ('move_id', '=', False),
        ]

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        res = super()._prepare_invoice_lines(fiscal_position)

        Analytic = self.env['account.analytic.line']
        FiscalPos = self.env['account.fiscal.position']
        fiscal_position = FiscalPos.browse(fiscal_position)
        start_date, end_date = self._prepare_invoice_variable_dates()

        domain = self._prepare_invoice_analytic_domain(start_date, end_date)
        analytic_lines = Analytic.search(domain)
        inv_lines = {}
        for line in analytic_lines:
            key = (line.product_id, line.product_uom_id)
            inv_lines.setdefault(
                key,
                {'analytic_account_id': self.id,
                 'product_id': line.product_id.id,
                 'name': self._prepare_invoice_variable_name(line),
                 'uom_id': line.product_uom_id.id,
                 'quantity': 1,
                 'price_unit': 0,
                 })
            inv_line = inv_lines[key]
            inv_line['price_unit'] += line.amount

        for key, value in inv_lines.items():
            new_line = self.env['sale.subscription.line'].new(value)
            res.append(
                (0, 0, self._prepare_invoice_line(new_line, fiscal_position))
            )
        return res

    def _prepare_invoice(self):
        """
        Set the last invoice date.

        Done when an recurring invoice is prepared.
        The _prepare_invoice() method is not called
        by the line prorating features, and so doesn't
        trigger setting this date.
        """
        invoicing_date = self.recurring_next_date
        values = super()._prepare_invoice()
        self.recurring_last_date = invoicing_date
        return values
