# Copyright (C) 2021 - TODAY, Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class POBackorderWizard(models.TransientModel):
    _name = "pobackorder.report.wizard"
    _description = "PO Backorder Report Wizard"

    def action_print_report(self):
        data = self.env["purchase.order.line"].search(
            [
                "&",
                ("product_type", "=", "product"),
                "|",
                ("bo_value", "!=", 0),
                ("uigr_value", "!=", 0),
            ]
        )
        return self.env.ref(
            "purchase_backorder.action_po_backorder_report"
        ).report_action(data)
