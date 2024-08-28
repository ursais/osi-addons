# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def create_sale_order(self):
        res = super().create_sale_order()
        self.blanket_order_id.sudo().action_mps_replenish(
            self.blanket_order_id.line_ids
        )
        return res
