# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_line_vals(self, line):
        vals = super()._prepare_so_line_vals(line)
        bom = self.env["mrp.bom"].search(
            [("product_id", "=", line.product_id.id)], limit=1
        )
        vals.update(bom_id=bom.id)
        return vals
