# Import Odoo libs
from odoo import api,fields, models


class MRPBom(models.Model):
    """Add the suggested margin field to product category."""

    _inherit = "mrp.bom"

    # COLUMNS #####

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        price_review_obj = self.env["product.price.review"]
        for result in results:
            if result.type == "phantom" and sum(result.bom_line_ids.mapped("product_id.price_review_count")) > 1:
                open_price_reivew = price_review_obj.search([("product_id","=",result.product_id.id),("state","in",["draft","in_progress"])])
                if not open_price_reivew:
                    price_review = price_review_obj.create({"product_id":result.product_id.id})
        return results
