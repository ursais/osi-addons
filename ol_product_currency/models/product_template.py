# Import Odoo libs
from odoo import api, models


class ProductTemplate(models.Model):
    """Inherit product template to override compute currency_id method"""

    _inherit = "product.template"

    @api.depends("company_id")
    @api.depends_context("company")
    def _compute_currency_id(self):
        """
        The core method first looks at company_id.currencly_id
        on product, then looks for the main company either by id base.main_company and
        if that doesn't exist, the first company in the list of companies.

        This means that if no company_id is set on the product (eg. Global Product),
        The currency is always the main companies currency.

        The cost_currency_id field computes based on company_id or env company so we
        are overriding this method to do the same as that field. This should reduce
        confusion when users look at the product and will now see the sale price in the
        correct currency.
        """
        # Get the currency ID of the current environment's company
        env_currency_id = self.env.company.currency_id.id
        for template in self:
            # Set the currency_id to the company's currency_id if available,
            # otherwise, use the environment's company currency_id
            template.currency_id = template.company_id.currency_id.id or env_currency_id
