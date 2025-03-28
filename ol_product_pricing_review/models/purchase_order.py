# Import Odoo libs
from odoo import _, fields, models


class PurchaseOrder(models.Model):
    """Inherit purchase order to create price review if doesn't exist"""

    _inherit = "purchase.order"

    # COLUMNS ##########

    price_review_count = fields.Integer(
        string="Price Reviews",
        compute="_compute_price_review_count",
    )

    # END ##########
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
            product.product_tmpl_id.sudo()._create_or_update_price_review(
                product.product_tmpl_id
            )

        return res

    def _compute_price_review_count(self):
        for order in self:
            # Count price reviews in `new` or `in_progress` for products in the purchase order
            order.price_review_count = self.env["product.price.review"].search_count(
                [
                    ("product_id", "in", order.order_line.product_id.ids),
                    ("state", "in", ["new", "in_progress"]),
                ]
            )

    def action_open_price_reviews(self):
        self.ensure_one()
        # Search price reviews in `new` or `in_progress` state for this purchase order
        price_reviews = self.env["product.price.review"].search(
            [
                ("product_id", "in", self.order_line.product_id.ids),
                ("state", "in", ["new", "in_progress"]),
            ]
        )
        if len(price_reviews) == 1:
            # If there is only one price review, open the form view
            return {
                "type": "ir.actions.act_window",
                "name": _("Price Review"),
                "view_mode": "form",
                "res_model": "product.price.review",
                "res_id": price_reviews.id,
                "target": "current",
            }
        elif price_reviews:
            # If there are multiple price reviews, open the list view
            return {
                "type": "ir.actions.act_window",
                "name": _("Price Reviews"),
                "view_mode": "tree,form",
                "res_model": "product.price.review",
                "domain": [
                    ("id", "in", price_reviews.ids),
                ],
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window_close",
        }

    # END ##########
