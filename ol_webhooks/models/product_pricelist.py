# Import Python libs

# Import Odoo libs
from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def write(self, values):
        """
        If certain field change on a Pricelist Item trigger a webhook event on the related products
        """
        # TODO: The pricing webhook work will be done separately as we need to understand the pricing engine workflow in Odoo17 and how odoo needs to communicate data to outside systems
        # fields = [
        #     "product_tmpl_id",
        #     "product_id",
        #     "min_quantity",
        #     "compute_price",
        #     "fixed_price",
        #     "percent_price",
        # ]
        # if [field_name for field_name in values.keys() if field_name in fields]:
        #     product_tmp_ids = self.mapped("product_tmpl_id") | self.mapped(
        #         "product_id.product_tmpl_id"
        #     )
        #     product_tmp_ids.with_context(
        #         force_trigger_price_webhook_event=True
        #     ).trigger_price_webhook_event(values={})
        return super().write(values)
