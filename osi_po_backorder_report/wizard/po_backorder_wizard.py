# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class POBackorderWizard(models.TransientModel):

    _name = "pobackorder.report.wizard"
    _description = "PO Backorder Report Wizard"

    def action_print_report(self, data):
        data = self.env['purchase.order.line'].search(
            ['|', ('bo_value', '!=', 0), ('uigr_value', '!=', 0)])
        return self.env.ref(
            'osi_po_backorder_report.action_po_backorder_report').\
            report_action(data)
