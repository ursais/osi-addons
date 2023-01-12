# Copyright (C) 2023 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Rma(models.Model):
    _inherit = "rma"

    can_generate_return = fields.Boolean(
        compute="_compute_can_generate_return",
        string="Can Generate Return Label",
    )

    def _compute_can_generate_return(self):
        for rma in self:
            rma.can_generate_return = False
            if self.reception_move_id.picking_id.carrier_id.can_generate_return:
                rma.can_generate_return = True

    def action_print_return_label(self):
        for rma in self:
            if rma.reception_move_id:
                self.ensure_one()
                rma.reception_move_id.picking_id.print_return_label()
                message = self.env["mail.message"].search(
                    [
                        ("model", "=", "stock.picking"),
                        ("res_id", "=", rma.reception_move_id.picking_id.id),
                        ("message_type", "=", "notification"),
                        ("body", "ilike", "Shipment created"),
                    ],
                    limit=1,
                )
                if message:
                    message.copy({"model": "rma", "res_id": rma.id})
