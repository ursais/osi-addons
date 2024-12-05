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

    # END #########
