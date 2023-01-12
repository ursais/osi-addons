# Copyright (C) 2023 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends("carrier_id", "move_ids_without_package")
    def _compute_return_picking(self):
        res = super()._compute_return_picking()
        for picking in self:
            rmas = self.env["rma"].search([("reception_move_id", "=", picking.id)])
            if (
                len(rmas) > 0
                and picking.carrier_id
                and picking.carrier_id.can_generate_return
            ):
                picking.is_return_picking = True
            elif picking.carrier_id and picking.carrier_id.can_generate_return:
                picking.is_return_picking = any(
                    m.origin_returned_move_id for m in picking.move_ids_without_package
                )
            else:
                picking.is_return_picking = False
        return res
