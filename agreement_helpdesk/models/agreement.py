# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    def _compute_ticket_count(self):
        for agreement in self:
            agreement.ticket_count = self.env["helpdesk.ticket"].search_count(
                [("agreement_id", "=", agreement.id)]
            )

    ticket_count = fields.Integer(compute="_compute_ticket_count", string="# Tickets")

    def action_view_ticket(self):
        for agreement in self:
            ticket_ids = self.env["helpdesk.ticket"].search(
                [("agreement_id", "=", agreement.id)]
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
