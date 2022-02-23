# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    helpdesk_ticket_ids = fields.Many2many(
        "helpdesk.ticket",
        "sale_helpdesk_ticket_rel",
        "sale_id",
        "ticket_id",
        string="Tickets",
        copy=False,
    )
    ticket_count = fields.Integer(
        string="Ticket Count", compute="_compute_ticket_count"
    )

    def _compute_ticket_count(self):
        for order in self:
            order.ticket_count = self.env["helpdesk.ticket"].search_count(
                [("sale_ids", "in", order.ids)]
            )

    def create_ticket(self):
        self.ensure_one()
        ticket_id = self.env["helpdesk.ticket"].create(
            {
                "name": self.name,
                "partner_id": self.partner_id.id,
                "user_id": self.user_id.id,
                "partner_email": self.partner_id.email,
                "description": self.note,
            }
        )
        ticket_id.sale_ids = [(6, 0, self.ids)]
        return {
            "name": _("Create Ticket"),
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "views": [[False, "form"]],
            "res_id": ticket_id.id,
        }

    def action_view_tickets(self):
        for order in self:
            ticket_ids = self.env["helpdesk.ticket"].search(
                [("sale_ids", "in", order.ids)]
            )
            action = self.env.ref("helpdesk.helpdesk_ticket_action_main_tree").read()[0]
            action["context"] = {}
            if len(ticket_ids) == 1:
                action["views"] = [
                    (self.env.ref("helpdesk.helpdesk_ticket_view_form").id, "form")
                ]
                action["res_id"] = ticket_ids.ids[0]
            else:
                action["domain"] = [("id", "in", ticket_ids.ids)]
            return action
