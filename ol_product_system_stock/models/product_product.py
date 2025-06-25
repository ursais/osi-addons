# Import Python libs

# Import Odoo libs
from odoo import models


class ProductProduct(models.Model):
    """
    Additions and overrides to templates to support product configuration
    """

    _inherit = 'product.product'

    def get_systems_containing_these_components(self, company=False):

        # All found product template IDs
        product_template_ids = []

        # First get a dataset for the related systems
        product_template_data = self.get_systems_data_containing_these_components(company=company)

        # Collect the unique Product Template IDs for the given company
        for _, tids in product_template_data.items():
            product_template_ids += list(tids)

        # Make sure the list of IDs are unique
        product_template_ids = list(set(product_template_ids))

        # Find the records
        return self.env['product.template'].browse(product_template_ids)
