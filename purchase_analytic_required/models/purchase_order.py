# Copyright 2024 Open Source Integrators Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _check_analytic_required_on_lines(self):
        """
        Check if analytic distribution is required on purchase order lines
        based on the account's analytic policy.
        """
        for order in self:
            if order.state in ['done', 'cancel']:
                continue
                
            missing_analytic_lines = []
            for line in order.order_line:
                if not line.product_id:
                    continue
                    
                # Get the expense account for the product
                account = line.product_id.property_account_expense_categ_id
                if not account:
                    account = line.product_id.categ_id.property_account_expense_categ_id
                
                if not account:
                    continue
                    
                # Check if analytic is required for this account
                analytic_policy = account._get_analytic_policy()
                if analytic_policy in ['always', 'posted'] and not line.analytic_distribution:
                    missing_analytic_lines.append({
                        'line': line,
                        'product': line.product_id.display_name,
                        'account': account.display_name,
                    })
            
            if missing_analytic_lines:
                error_msg = _(
                    "Analytic distribution is required for the following lines:\n\n"
                )
                for item in missing_analytic_lines:
                    error_msg += _(
                        "• Product: %(product)s (Account: %(account)s)\n"
                    ) % {
                        'product': item['product'],
                        'account': item['account'],
                    }
                error_msg += _(
                    "\nPlease set the analytic distribution on these lines "
                    "or on the purchase order header to apply to all lines."
                )
                raise ValidationError(error_msg)

    def button_confirm(self):
        """Override to check analytic requirements before confirming."""
        self._check_analytic_required_on_lines()
        return super().button_confirm()

    def _prepare_invoice(self):
        """Override to check analytic requirements before creating invoice."""
        self._check_analytic_required_on_lines()
        return super()._prepare_invoice()
