# Import Odoo Libs
from odoo import models, fields
from odoo.tools import float_compare
from odoo.tools.misc import format_date


class MrpProductionBatch(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "mrp.production.batch"

    # COLUMNS #####

    has_constrained_component = fields.Boolean(
        compute="_compute_has_constrained_component",
        help="Helper field to inform the user that there is a component in MOs on the batch that are marked constrained",
    )

    # END #########
    # METHODS #####

    def _compute_has_constrained_component(self):
        for batch in self:
            has_constrained_component = False
            valid_productions = batch.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            all_raw_moves = any(
                valid_productions.move_raw_ids.filtered(
                    lambda l: l.product_id.is_constrained
                )
            )
            if all_raw_moves:
                has_constrained_component = True
            batch.has_constrained_component = has_constrained_component

    def _compute_components_availability_details(self):
        """Override the Method to add * in product display name where is_constrained is set."""
        """Computes batch-level component availability based on MO statuses."""
        for batch in self:
            batch.components_availability_details = ""

            valid_productions = batch.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            if not valid_productions:
                continue

            # Fetch all raw moves and ensure calculations are up to date
            all_raw_moves = valid_productions.move_raw_ids
            all_raw_moves._fields["forecast_availability"].compute_value(all_raw_moves)

            product_status_map = {}

            for move in all_raw_moves:
                product = move.product_id
                display_string = (
                    "*" + product.default_code
                    if product.is_constrained
                    else product.default_code
                )
                if product.id in product_status_map:
                    continue  # Skip duplicate product

                required_qty = 0 if move.state == "draft" else move.product_qty
                if (
                    float_compare(
                        move.forecast_availability,
                        required_qty,
                        precision_rounding=product.uom_id.rounding,
                    )
                    == -1
                ):
                    product_status_map[product.id] = f"{display_string}: Not Available"

                if move.forecast_expected_date:
                    product_status_map[product.id] = (
                        f"{display_string}: Exp. {format_date(self.env, move.forecast_expected_date)}"
                    )

            # Populate the details field
            batch.components_availability_details = "\n".join(
                product_status_map.values()
            )

    # END #########
