# Copyright 2024 Open Source Integrators Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order_line"

    @api.constrains('analytic_distribution', 'product_id')
    def _check_analytic_required(self):
        """
        Check if analytic distribution is required based on the product's account
        analytic policy.
        """
        for line in self:
            if not line.product_id or line.order_id.state in ['done', 'cancel']:
                continue
                
            # Get the expense account for the product
            account = line.product_id.property_account_expense_categ_id
            if not account:
                account = line.product_id.categ_id.property_account_expense_categ_id
            
            if not account:
                continue
                
            # Check if analytic is required for this account
            analytic_policy = account._get_analytic_policy()
            if analytic_policy == 'always' and not line.analytic_distribution:
                raise ValidationError(_(
                    "Analytic distribution is required for product '%(product)s' "
                    "because account '%(account)s' has analytic policy set to 'Always'."
                ) % {
                    'product': line.product_id.display_name,
                    'account': account.display_name,
                })
            elif analytic_policy == 'never' and line.analytic_distribution:
                raise ValidationError(_(
                    "Analytic distribution is not allowed for product '%(product)s' "
                    "because account '%(account)s' has analytic policy set to 'Never'."
                ) % {
                    'product': line.product_id.display_name,
                    'account': account.display_name,
                })
