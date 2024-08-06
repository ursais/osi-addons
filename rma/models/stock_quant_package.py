# Copyright (C) 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class QuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _allowed_to_move_between_transfers(self):
        res = super()._allowed_to_move_between_transfers()
        return res and self.location_id != self.env.ref(
            "stock.stock_location_customers"
        )
