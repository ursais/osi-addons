# Import Odoo libs
from odoo import api, models


class MRPBom(models.Model):
    """Create a new price review when bom kits are created if one doesn't exist."""

    _inherit = "mrp.bom"

    # METHODS #####

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        price_review_obj = self.env["product.price.review"]
        for result in results:
            # Check if the BOM type is 'phantom' (Kit) and if the sum of price
            # review counts is greater than 1
            if (
                result.type == "phantom"
                and sum(result.bom_line_ids.mapped("product_id.price_review_count")) > 1
            ):
                # Search for open price reviews for the product
                open_price_reivew = price_review_obj.search(
                    [
                        ("product_id", "=", result.product_id.id),
                        ("state", "in", ["draft", "in_progress"]),
                    ]
                )

                # If no open price review exists, create a new one
                if not open_price_reivew:
                    price_review_obj.create({"product_id": result.product_id.id})
        return results

    # END #####
