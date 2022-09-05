# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Rma(models.Model):
    _inherit = "rma"

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Helpdesk Ticket",
        readonly=True,
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self.ticket_id = False
        return res

    @api.onchange("ticket_id")
    def _onchange_order_id(self):
        self.product_id = False
