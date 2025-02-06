# Import Odoo libs
from odoo import api, fields, models


class MrpProductionBatch(models.Model):
    """Inherit Batch to add rush order status."""

    _inherit = "mrp.production.batch"

    # COLUMNS #########

    rush_order = fields.Boolean(
        "Rush Order",
        compute="_compute_rush_order",
        store=True,
    )

    # END #########
    # METHODS #####

    @api.depends(
        "production_ids.sale_order_id.rush_order",
        "production_ids.state",
    )
    def _compute_rush_order(self):
        for record in self:
            record.rush_order = False

            if record.production_ids:
                record.rush_order = any(
                    production.state != "cancel" and production.rush_order
                    for production in record.production_ids
                )

    @api.depends("is_delayed", "is_planned", "rush_order")
    def _compute_tags(self):
        # First call the original method in the base model using super()
        super()._compute_tags()  # This will handle is_delayed and is_planned tags

        for record in self:
            rush_order_tag = self.env["mrp.production.batch.tag"].search(
                [("name", "=", "Rush Order")], limit=1
            )

            # Add or remove Rush Order tag based on rush_order
            if record.rush_order and rush_order_tag:
                if rush_order_tag.id not in record.tag_ids.ids:
                    # Add Rush Order tag
                    record.tag_ids = [(4, rush_order_tag.id)]  # Add to existing tags
            elif not record.rush_order and rush_order_tag:
                if rush_order_tag.id in record.tag_ids.ids:
                    # Remove Rush Order tag
                    record.tag_ids = [
                        (3, rush_order_tag.id)
                    ]  # Remove from existing tags

    # END #########
