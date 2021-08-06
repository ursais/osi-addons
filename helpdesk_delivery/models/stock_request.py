# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockRequest(models.Model):
    _inherit = "stock.request"

    carrier_id = fields.Many2one("delivery.carrier", string="Delivery Method")

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        if not res.get("carrier_id", False):
            res.update(
                {
                    "carrier_id": self.helpdesk_ticket_id.carrier_id.id or False,
                }
            )
        return res

    def _prepare_procurement_group_values(self):
        if self.helpdesk_ticket_id:
            order = self.env["helpdesk.ticket"].browse(self.helpdesk_ticket_id.id)
            return {
                "name": order.name,
                "helpdesk_ticket_id": order.id,
                "move_type": "direct",
            }
        else:
            return {}
