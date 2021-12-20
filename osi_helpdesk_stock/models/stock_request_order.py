# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    helpdesk_ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Ticket", ondelete="cascade", index=True, copy=False
    )

    @api.onchange("warehouse_id", "direction", "helpdesk_ticket_id")
    def _onchange_location_id(self):
        super()._onchange_location_id()
        if self.helpdesk_ticket_id:
            if self.direction == "outbound":
                # Inventory location of the ticket
                self.location_id = self.helpdesk_ticket_id.inventory_location_id.id
            else:
                # Otherwise the stock location of the warehouse
                self.location_id = self.helpdesk_ticket_id.warehouse_id.lot_stock_id.id
        self.change_childs()

    def change_childs(self):
        super().change_childs()
        if not self._context.get("no_change_childs", False):
            for line in self.stock_request_ids:
                line.helpdesk_ticket_id = self.helpdesk_ticket_id.id

    def _prepare_procurement_group_values(self):
        if self.helpdesk_ticket_id:
            ticket = self.env["helpdesk.ticket"].browse(self.helpdesk_ticket_id.id)
            return {
                "name": ("#" + str(ticket.id)),
                "helpdesk_ticket_id": ticket.id,
                "move_type": "direct",
            }
        else:
            return {}

    def action_confirm(self):
        if self.helpdesk_ticket_id and not self.procurement_group_id:
            ticket = self.env["helpdesk.ticket"].browse(self.helpdesk_ticket_id.id)
            group = self.env["procurement.group"].search(
                [("helpdesk_ticket_id", "=", self.helpdesk_ticket_id.id)],
                limit=1, order="id desc")
            if not group:
                values = self._prepare_procurement_group_values()
                group = self.env["procurement.group"].create(values)
            self.procurement_group_id = group.id
            self.change_childs()
        return super().action_confirm()
