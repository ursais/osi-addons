from odoo import fields, models


class ProducProduct(models.Model):
    _inherit = "product.product"

    price_review_count = fields.Integer(
        "# Price Reviews",
        compute="_compute_price_review",
    )

    def _compute_price_review(self):
        """Computes the number of price reviews to show in the smart button."""
        for rec in self:
            rec.price_review_count = self.env["product.price.review"].search_count(
                [
                    ("product_id", "=", rec.id),
                ]
            )

    def action_view_price_reviews(self):
        """Action to open related price reviews from smart button."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ol_product_pricing_review.product_open_price_review"
        )
        action["context"] = {
            "default_product_id": self.id or False,
            "search_default_review_state_draft": True,
            "search_default_review_state_in_progress": True,
        }
        action["domain"] = [("product_id", "in", self.ids)]
        return action

    def action_price_review(self):
        """Action for the Price Review button, opens an existing
        review (Draft/In Progress), otherwise opens a new one."""
        open_review = self.env["product.price.review"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("product_id", "=", self.id),
                ("state", "not in", ("reject", "validated")),
            ],
            limit=1,
        )
        view = self.env.ref("ol_product_pricing_review.product_price_review_form_view")
        if open_review:
            return {
                "res_model": "product.price.review",
                "type": "ir.actions.act_window",
                "context": {},
                "view_mode": "form",
                "view_type": "form",
                "res_id": open_review.id,
                "view_id": view.id,
                "target": "current",
            }
        else:
            return {
                "res_model": "product.price.review",
                "type": "ir.actions.act_window",
                "context": {"default_product_id": self.id},
                "view_mode": "form",
                "view_type": "form",
                "view_id": view.id,
                "target": "current",
            }
