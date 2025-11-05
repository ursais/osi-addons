import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


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
                        lambda m: m.state in ("assigned", "partially_available")
                        and m.product_id.type == "product"
                    ):
                        # Find all active mrp.production records with this product in raw materials
                        productions = self.env["mrp.production"].search(
                            [
                                (
                                    "state",
                                    "not in",
                                    ("draft", "cancel", "done", "to_close"),
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
                    .get_param("mrp_batch.enable_delay_component_availability", "False")
                )
                for batch in batches_to_recompute:
                    if enable_component_available_delay and enable_component_available_delay.lower() in ("true", "1", "yes"):
                        batch.with_delay()._compute_components_availability()
                    else:
                        batch._compute_components_availability()

            return res
        else:
            return super().write(vals)

    # def write(self, vals):
    #     # Check if the 'scheduled_date' field is being changed
    #     if "scheduled_date" in vals:
    #         # Call the super method to perform the actual write
    #         res = super().write(vals)

    #         # Collect batches to recompute
    #         batches_to_recompute = set()
    #         for picking in self:
    #             for move in picking.move_line_ids.filtered(lambda m: m.state in ('assigned', 'partially_available') and m.product_id.type == 'product'):
    #                 # Find all active mrp.production records with the product in raw_move_ids
    #                 productions = self.env["mrp.production"].search(
    #                     [
    #                         (
    #                             "state",
    #                             "not in",
    #                             ("draft", "cancel", "done", "to_close"),
    #                         ),
    #                         ("move_raw_ids.product_id", "=", move.product_id.id),
    #                     ]
    #                 )
    #                 for production in productions:
    #                     if production.mrp_batch_id:
    #                         batches_to_recompute.add(production.mrp_batch_id)

    #         # Recompute the batches
    #         for batch in batches_to_recompute:
    #             enable_component_available_delay = (
    #                 self.env["ir.config_parameter"]
    #                 .sudo()
    #                 .get_param("mrp_batch.enable_delay_component_availability", "True")
    #                 == "True"
    #             )
    #             if enable_component_available_delay:
    #                 batch.with_delay()._compute_components_availability()
    #             else:
    #                 batch._compute_components_availability()

    #         return res
    #     else:
    #         return super().write(vals)
