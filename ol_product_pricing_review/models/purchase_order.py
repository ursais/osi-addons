# Import Odoo libs
from odoo import models


class PurchaseOrder(models.Model):
    """Inherit purchase order to create price review if doesn't exist"""

    _inherit = "purchase.order"

    # METHODS ##########

    def button_confirm(self):
        res = super().button_confirm()

        # Get all relevant products from order lines across orders
        product_ids = self.mapped("order_line.product_id")

        # Check for products without price reviews in batch
        products_without_reviews = self.env["product.product"].browse(
            self.env["product.price.review"]
            .search([("product_id", "in", product_ids.ids)])
            .mapped("product_id")
        )
        products_to_create_review = product_ids - products_without_reviews

        # Create or update price reviews for the relevant products
        for product in products_to_create_review:
            product.product_tmpl_id._create_or_update_price_review(
                product.product_tmpl_id
            )

        return res

    # END ##########
