# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MrpProductionSchedule(models.Model):
    _inherit = "mrp.production.schedule"

    def get_production_schedule_view_state(self):
        """
        Extends the functionality of the method to modify the production
        schedule view state.

        - Retrieves the production schedule view from the parent class.
        - Checks the current context for specific MPS (Master Production
          Schedule) parameters like date, ID, and product.
        - Updates the forecast information of the schedule line if it matches
          the provided MPS date and product.

        :return: Modified production schedule view state.
        """
        # Get the original production schedule view state from the inherited class
        res = super().get_production_schedule_view_state()

        # Retrieve the current context for the MPS (Master Production Schedule) data
        context = dict(self._context)

        # Extract specific MPS-related values from the context
        mps_date = context.get("mps_date")
        mps_id = context.get("mps_id")
        product_id = context.get("product_id")

        # Loop through the schedule lines in the result
        for line in res:
            # Check if the current line matches the MPS ID and the product ID
            if line.get("id") == mps_id and line.get("product_id")[0] == product_id:
                # Loop through the forecast entries for the matched schedule line
                for forecast in line.get("forecast_ids"):
                    # If the forecast's start date matches the MPS date
                    if forecast.get("date_start") == mps_date:
                        # Update forecast details to trigger replenishment and
                        # mark it as editable
                        forecast.update(
                            {
                                "forced_replenish": True,
                                "replenish_qty_updated": True,
                                "to_replenish": True,
                                "is_edit_forcast_qty": True,
                            }
                        )

        # Return the modified production schedule view state
        return res
