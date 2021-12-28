# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    fsm_location_id = fields.Many2one("fsm.location", string="FSM Location")
    helpdesk_ticket_id = fields.Many2one("helpdesk.ticket", string="Ticket")

    @api.model
    def create(self, vals):
        if vals.get("fsm_order_id"):
            fsm_order = self.env["fsm.order"].browse(vals["fsm_order_id"])
            vals.update(
                {
                    "helpdesk_ticket_id": fsm_order.ticket_id.id or False,
                    "fsm_location_id": fsm_order.location_id.id or False,
                }
            )
        elif vals.get("helpdesk_ticket_id", False):
            ticket = self.env["helpdesk.ticket"].browse(vals["helpdesk_ticket_id"])
            vals.update({"fsm_location_id": ticket.fsm_location_id.id or False})
        return super().create(vals)

    @api.onchange("warehouse_id", "direction", "fsm_order_id", "helpdesk_ticket_id")
    def _onchange_location_id(self):
        super()._onchange_location_id()
        # FSM Order takes priority over Helpdesk Ticket
        order = self.fsm_order_id or self.helpdesk_ticket_id
        if order:
            if self.direction == "outbound":
                self.location_id = order.inventory_location_id.id
            else:
                self.location_id = order.warehouse_id.lot_stock_id.id
            self.change_childs()

    def change_childs(self):
        super().change_childs()
        if not self._context.get("no_change_childs", False):
            for line in self.stock_request_ids:
                line.fsm_order_id = self.fsm_order_id.id
                line.helpdesk_ticket_id = self.fsm_order_id.ticket_id.id or False
                if not line.helpdesk_ticket_id:
                    line.helpdesk_ticket_id = self.helpdesk_ticket_id

    def write(self, vals):
        if vals.get("fsm_order_id"):
            order = self.env["fsm.order"].browse(vals["fsm_order_id"])
            vals.update(
                {
                    "helpdesk_ticket_id": order.ticket_id.id or False,
                    "fsm_location_id": order.fsm_location_id.id or False,
                }
            )
        return super().write(vals)

    def _prepare_procurement_group_values(self):
        res = super()._prepare_procurement_group_values()
        res.update(
            {
                "name": self.fsm_order_id.name,
                "fsm_order_id": self.fsm_order_id.id,
                "helpdesk_ticket_id": self.fsm_order_id.ticket_id.id or False,
            }
        )
        return res
