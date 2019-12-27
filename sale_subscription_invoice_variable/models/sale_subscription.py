# Copyright (C) 2019, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta
from odoo import models, api


class SaleSubscription(models.Model):

    _inherit = 'sale.subscription'

    def _prepare_invoice_variable_dates(self):
        """
        The dates for the previous billing period.
        Based on the implementation of _prepare_invoice_data().
        """
        self.ensure_one()
        next_date = fields.Date.from_string(self.recurring_next_date)
        if not next_date:
            raise UserError(
                _('Please define Date of Next Invoice of "%s".')
                % (self.display_name,))
        periods = {
            'daily': 'days', 'weekly': 'weeks',
            'monthly': 'months', 'yearly': 'years'}
        start_date = next_date - relativedelta(
            **{periods[self.recurring_rule_type]: self.recurring_interval})
        end_date = next_date - relativedelta(days=1)
        return start_date, end_date

    @api.model
    def _prepare_invoice_variable_name(self, analytic_line):
        """Returns the description to use for the invoice line"""
        return analytic_line.product_id.name

    def _prepare_invoice_lines(self, fiscal_position):
        res = super()._prepare_invoice_lines(fiscal_position)
        import pudb; pu.db

        self.ensure_one()
        Analytic = self.env['account.analytic.line']
        FiscalPos = self.env['account.fiscal.position']
        fiscal_position = FiscalPos.browse(fiscal_position)
        start_date, end_date = self._prepare_invoice_variable_dates()
        domain = [
            ('account_id', '=', self.analytic_account_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('amount', '!=', 0.0)
        ]
        analytic_lines = Analytic.search(domain)
        inv_lines = {}
        for line in analytic_lines:
            key = (line.product_id, line.product_uom_id)
            inv_lines.setdefault(
                key,
                {'analytic_account_id': line.account_id.id,
                 'product_id': line.product_id.id,
                 'name': self._prepare_invoice_variable_name(line),
                 'uom_id': line.product_uom_id.id,
                 'price_unit': 0,
                 })
            inv_line = inv_lines[key]
            inv_line['price_unit'] += line.amount

        for key, value in inv_lines:
            new_line = Analytic.new(value)
            res.append(
                [(0, 0, self._prepare_invoice_line(new_line, fiscal_position))]
        return res
