# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpProductionSchedule(models.Model):
    _inherit = "mrp.production.schedule"

    prod_id = fields.Integer(string="Product ID", related="product_id.id")

    def get_production_schedule_view_state(self):
        res = super().get_production_schedule_view_state()
        mps_date = self._context.get("mps_date")
        self._context.get("mps_qty")
        mps_id = self._context.get("mps_id")
        product_id = self._context.get("product_id")
        if mps_id and mps_date:
            for line in res:
                if line.get("id") == mps_id and line.get("product_id")[0] == product_id:
                    for forcast in line.get("forecast_ids"):
                        if forcast.get("date_start") == mps_date:
                            forcast.update(
                                {
                                    "forced_replenish": True,
                                    "replenish_qty_updated": True,
                                    "to_replenish": True,
                                }
                            )
        return res
