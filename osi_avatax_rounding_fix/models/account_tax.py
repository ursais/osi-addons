from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None, is_company_currency_requested=False):
        vals = super()._prepare_tax_totals(base_lines, currency, tax_lines, is_company_currency_requested)
        if vals.get('amount_untaxed'):
            vals['amount_untaxed'] = round(vals['amount_untaxed'], 2)
        if vals.get('amount_total'):
            vals['amount_total'] = round(vals['amount_total'], 2)
        return vals
