# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    use_helpdesk_sale_orders = fields.Boolean(
        string="Sale Order activated on Team",
        related="team_id.use_sale_orders",
        readonly=True,
    )
    sale_ids = fields.Many2many(
        "sale.order",
        "sale_helpdesk_ticket_rel",
        "ticket_id",
        "sale_id",
        copy=False,
    )
    sale_count = fields.Integer(
        string="Sales Order Count", compute="_compute_sale_order_count"
    )

    def _compute_sale_order_count(self):
        for ticket in self:
            ticket.sale_count = self.env["sale.order"].search_count(
                [("helpdesk_ticket_ids", "in", ticket.id)]
            )

    def create_sale_order(self):
        self.ensure_one()
        if self.partner_id.sale_warn == "block":
            msg = "Warning for Partner {}\n\n{}".format(
                self.partner_id.name, self.partner_id.sale_warn_msg
            )
            raise ValidationError(_(msg))
        order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "user_id": self.user_id.id,
                "note": self.description,
            }
        )
        order_id.helpdesk_ticket_ids = [(6, 0, self.ids)]
        return {
            "name": _("Create Sales Order"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order_id.id,
        }

    def action_view_sale_order(self):
        for helpdesk_ticket_id in self:
            sale_order_ids = self.env["sale.order"].search(
                [("helpdesk_ticket_ids", "in", helpdesk_ticket_id.ids)]
            )
            action = self.env.ref("sale.action_orders").read()[0]
            action["context"] = {}
            if len(sale_order_ids) == 1:
                action["views"] = [(self.env.ref("sale.view_order_form").id, "form")]
                action["res_id"] = sale_order_ids.ids[0]
            else:
                action["domain"] = [("id", "in", sale_order_ids.ids)]
            return action
