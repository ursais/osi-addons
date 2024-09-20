from odoo import _, models


class TierReview(models.Model):
    _inherit = "tier.review"

    def write(self, vals):
        # Prevent recursion by checking the context
        if self.env.context.get("prevent_recursion"):
            return super().write(vals)

        res = super().write(vals)

        for review in self:
            if (
                "status" in vals
                and review.status in ("rejected", "approved")
                and review.model == "sale.order"
                and review.res_id
            ):
                # Fetch the related sale order
                sale_order = self.env["sale.order"].browse(review.res_id)
                if sale_order:
                    message = _("Review  %s: '%s' by %s.") % (
                        "Approved" if vals["status"] == "approved" else "Rejected",
                        review.name,
                        review.done_by.display_name,
                    )
                    # Prevent recursion when posting the message
                    # Found during testing that this can happen in certain scenarios.
                    sale_order.with_context(prevent_recursion=True).message_post(
                        body=message
                    )

        return res
