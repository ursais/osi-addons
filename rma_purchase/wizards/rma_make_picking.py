# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaMakePicking(models.TransientModel):
    _inherit = "rma_make_picking.wizard"

    def _prepare_item(self, line):
        res = super()._prepare_item(line)
        res["purchase_order_line_id"] = line.purchase_order_line_id.id
        return res

    @api.model
    def _get_action(self, pickings, procurements):
        po_list = []
        for procurement in procurements:
            if procurement.purchase_id and procurement.purchase_id.id:
                po_list.append(procurement.purchase_id.id)
        if len(po_list):
            action = self.env.ref("purchase.purchase_rfq")
            result = action.sudo().read()[0]
            result["domain"] = [("id", "in", po_list)]
            return result
        else:
            action = super()._get_action(pickings, procurements)
            return action


class RmaMakePickingItem(models.TransientModel):
    _inherit = "rma_make_picking.wizard.item"

    purchase_order_line_id = fields.Many2one(
        "purchase.order.line", string="Purchase Line"
    )
