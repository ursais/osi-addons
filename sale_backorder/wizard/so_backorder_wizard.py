# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SOBackorderWizard(models.TransientModel):
    _name = "sobackorder.report.wizard"
    _description = "SO Backorder Report Wizard"

    def action_print_report(self):
        data = self.env["sale.order.line"].search(
            [
                "&",
                ("product_type", "=", "product"),
                "|",
                ("bo_value", "!=", 0),
                ("uigd_value", "!=", 0),
            ]
        )
        return self.env.ref("sale_backorder.action_so_backorder_report").report_action(
            data
        )
