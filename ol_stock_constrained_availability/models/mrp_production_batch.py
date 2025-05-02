# Import Odoo Libs
from odoo import models
from odoo.tools import float_compare


class MrpProductionBatch(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "mrp.production.batch"

    # METHOD #####

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
                    product_status_map[
                        product.id
                    ] = f"{display_string}: Exp. {format_date(self.env, move.forecast_expected_date)}"

            # Populate the details field
            batch.components_availability_details = "\n".join(
                product_status_map.values()
            )

    # END #####
