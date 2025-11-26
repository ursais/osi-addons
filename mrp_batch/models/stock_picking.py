
# Constants for state values
STATE_DONE = "done"
STATE_CANCEL = "cancel"
STATE_DRAFT = "draft"
STATE_ASSIGNED = "assigned"
STATE_PARTIALLY_AVAILABLE = "partially_available"

# Constants for config parameter keys
CONFIG_ENABLE_DELAY_COMPONENT_AVAILABILITY = CONFIG_ENABLE_DELAY_COMPONENT_AVAILABILITY

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    mrp_batch_id = fields.Many2one(
        "mrp.production.batch",
        string="MO Batch",
        help="Manufacturing batch this picking is linked to.",
    )

    def write(self, vals):
        # Check if the 'scheduled_date' field is being changed
        if "scheduled_date" in vals:
            res = super().write(vals)

            batches_to_recompute = set()

            for picking in self:
                # Only consider relevant pickings (incoming or internal to production/internal)
                if picking.picking_type_id.code in (
                    "incoming",
                    "internal",
                ) and picking.location_dest_id.usage in ("production", "internal"):
                    for move in picking.move_line_ids.filtered(
                        lambda m: m.state in (STATE_ASSIGNED, STATE_PARTIALLY_AVAILABLE)
                        and m.product_id.type == "product"
                    ):
                        # Find all active mrp.production records with this product in raw materials
                        productions = self.env["mrp.production"].search(
                            [
                                (
                                    "state",
                                    "not in",
                                    (STATE_DRAFT, STATE_CANCEL, STATE_DONE, STATE_TO_CLOSE),
                                ),
                                ("move_raw_ids.product_id", "=", move.product_id.id),
                            ]
                        )
                        for production in productions:
                            if production.mrp_batch_id:
                                batches_to_recompute.add(production.mrp_batch_id)

            # Recompute the batches
            if batches_to_recompute:
                enable_component_available_delay = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(CONFIG_ENABLE_DELAY_COMPONENT_AVAILABILITY)
                )
                for batch in batches_to_recompute:
                    if enable_component_available_delay and enable_component_available_delay.lower() in ("true", "1", "yes"):
                        batch.with_delay()._compute_components_availability()
                    else:
                        batch._compute_components_availability()

            return res
        else:
            return super().write(vals)



    #         return res
    #     else:
    #         return super().write(vals)
