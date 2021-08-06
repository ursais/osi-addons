# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockRequest(models.Model):
    _inherit = "stock.request"

    helpdesk_ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Ticket", ondelete="cascade", index=True, copy=False
    )

    @api.onchange("direction", "helpdesk_ticket_id")
    def _onchange_location_id(self):
        super()._onchange_location_id()
        if self.helpdesk_ticket_id:
            if self.direction == "outbound":
                # Inventory location of the ticket
                self.location_id = self.helpdesk_ticket_id.inventory_location_id.id
            else:
                # Otherwise the stock location of the warehouse
                self.location_id = self.helpdesk_ticket_id.warehouse_id.lot_stock_id.id

    def prepare_order_values(self, vals):
        picking_type_id = self.env["stock.picking.type"].search(
            [
                ("code", "=", "stock_request_order"),
                ("warehouse_id", "=", vals["warehouse_id"]),
            ],
            limit=1,
        )
        if not picking_type_id:
            picking_type_id = self.env["stock.picking.type"].search(
                [("code", "=", "stock_request_order")], limit=1
            )
        helpdesk_ticket = self.env["helpdesk.ticket"].browse(vals["helpdesk_ticket_id"])
        res = {
            "expected_date": vals["expected_date"],
            "picking_policy": vals["picking_policy"],
            "warehouse_id": vals["warehouse_id"],
            "direction": vals["direction"],
            "picking_type_id": picking_type_id.id,
            "location_id": helpdesk_ticket.warehouse_id.lot_stock_id.id,
        }
        if "helpdesk_ticket_id" in vals and vals["helpdesk_ticket_id"]:
            res.update({"helpdesk_ticket_id": vals["helpdesk_ticket_id"]})
        return res

    @api.model
    def create(self, vals):
        if (
            "helpdesk_ticket_id" in vals
            and vals.get("helpdesk_ticket_id", False)
            and not vals.get("order_id", False)
        ):
            ticket = self.env["helpdesk.ticket"].browse(vals["helpdesk_ticket_id"])
            ticket.request_stage = "draft"
            vals["warehouse_id"] = ticket.warehouse_id.id
            vals["location_id"] = (
                ticket.warehouse_id.lot_stock_id.id or ticket.inventory_location_id.id
            )
            picking_type_id = self.env["stock.picking.type"].search(
                [
                    ("code", "=", "stock_request_order"),
                    ("warehouse_id", "=", vals["warehouse_id"]),
                ],
                limit=1,
            )
            helpdesk_ticket = self.env["stock.request.order"].search(
                [
                    ("helpdesk_ticket_id", "=", vals["helpdesk_ticket_id"]),
                    ("warehouse_id", "=", vals["warehouse_id"]),
                    ("picking_type_id", "=", picking_type_id.id),
                    ("direction", "=", vals["direction"]),
                    ("state", "=", "draft"),
                ],
                order="id asc",
            )

            # User created a new SRO Manually
            if len(helpdesk_ticket) > 1:
                raise UserError(
                    _(
                        "There is already a Stock Request Order \
                                  with the same Helpdesk Ticket and \
                                  Warehouse that is in Draft state. Please \
                                  add this Stock Request there. \
                                  (%s)"
                    )
                    % helpdesk_ticket[0].name
                )
            # Made from an HT for the first time, create the SRO here
            elif not helpdesk_ticket and vals.get("helpdesk_ticket_id"):
                values = self.prepare_order_values(vals)
                vals["order_id"] = self.env["stock.request.order"].create(values).id
            # There is an SRO made from HT, assign here
            elif len(helpdesk_ticket) == 1 and vals.get("helpdesk_ticket_id"):
                vals["expected_date"] = helpdesk_ticket.expected_date
                vals["order_id"] = helpdesk_ticket.id
        return super().create(vals)

    def _prepare_procurement_group_values(self):
        if self.helpdesk_ticket_id:
            ticket = self.env["helpdesk.ticket"].browse(self.helpdesk_ticket_id.id)
            return {
                "name": ticket.name,
                "helpdesk_ticket_id": ticket.id,
                "move_type": "direct",
            }
        else:
            return {}

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        res.update(
            {
                "helpdesk_ticket_id": self.helpdesk_ticket_id.id,
                "partner_id": self.helpdesk_ticket_id.partner_id.id,
            }
        )
        return res

    def _action_confirm(self):
        for req in self:
            if (not req.procurement_group_id) and req.helpdesk_ticket_id:
                ticket = self.env["helpdesk.ticket"].browse(req.helpdesk_ticket_id.id)
                group = self.env["procurement.group"].search(
                    [("helpdesk_ticket_id", "=", ticket.id)]
                )
                if not group:
                    values = req._prepare_procurement_group_values()
                    group = self.env["procurement.group"].create(values)
                if req.order_id:
                    req.order_id.procurement_group_id = group.id
                req.procurement_group_id = group.id
                res = super(StockRequest, req)._action_confirm()
                ticket.request_stage = "open"
            else:
                res = super(StockRequest, req)._action_confirm()
        return res
