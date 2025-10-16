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

        product_ids = self.mapped("order_line.product_id")
        PriceReview = self.env["product.price.review"]

        # Find existing reviews for the products
        existing_reviews = PriceReview.search([("product_id", "in", product_ids.ids)])
        products_with_reviews = existing_reviews.mapped("product_id")

        # Find and reject any pending reviews directly
        pending_reviews = PriceReview.search(
            [
                ("product_id", "in", product_ids.ids),
                ("state", "=", "pending"),
            ]
        )
        if pending_reviews:
            pending_reviews.reject_button()
            pending_reviews.message_post(
                body=_(
                    "Pending price review automatically rejected due to "
                    "new Purchase Order confirmation."
                ),
                body_is_html=True,
            )

        # Determine which products need a new review:
        # - Products without any review
        # - Products whose pending review was just rejected
        products_to_create_review = (
            product_ids - products_with_reviews
        ) | pending_reviews.mapped("product_id")

        # Create or update price reviews for those products
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
                    ("state", "in", ["new", "in_progress", "pending"]),
                ]
            )

    def action_open_price_reviews(self):
        self.ensure_one()
        # Search price reviews in `new` or `in_progress` state for this purchase order
        price_reviews = self.env["product.price.review"].search(
            [
                ("product_id", "in", self.order_line.product_id.ids),
                ("state", "in", ["new", "in_progress", "pending"]),
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
