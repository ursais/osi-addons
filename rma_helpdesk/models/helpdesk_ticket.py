# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    rma_ids = fields.One2many(
        comodel_name="rma",
        inverse_name="ticket_id",
        string="RMAs",
        copy=False,
    )
    rma_count = fields.Integer(string="RMA count", compute="_compute_rma_count")

    def _compute_rma_count(self):
        for record in self:
            record.rma_count = len(self.rma_ids.ids)

    def create_rma(self):
        self.ensure_one()
        rma_model = self.env["rma"]
        vals_list = []
        for rec in self:
            vals = {
                "partner_id": rec.partner_id.id,
                "origin": rec.name,
                "company_id": rec.company_id.id,
                "product_id": rec.product_id.id,
                "description": rec.description,
                "ticket_id": rec.id,
            }
            vals_list.append(vals)
        rma = rma_model.create(vals_list)
        return rma

    def create_and_open_rma(self):
        self.ensure_one()
        rma = self.create_rma()
        if not rma:
            return
        action = self.sudo().env.ref("rma.rma_action").read()[0]
        if len(rma) > 1:
            action["domain"] = [("id", "in", rma.ids)]
        elif rma:
            action.update(
                res_id=rma.id,
                view_mode="form",
                view_id=False,
                views=False,
            )
        return action

    def action_view_rma(self):
        self.ensure_one()
        action = self.sudo().env.ref("rma.rma_action").read()[0]
        rma = self.rma_ids
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
                views=[],
            )
        else:
            action["domain"] = [("id", "in", rma.ids)]
        # reset context to show all related rma without default filters
        action["context"] = {}
        return action
