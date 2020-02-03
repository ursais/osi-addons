# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    @api.onchange('reason_code_id')
    def onchange_reason_code_id(self):
        if self.reason_code_id:
            self.analytic_account_id = self.reason_code_id.analytic_account_id
            self.analytic_segment_one_id = self.reason_code_id.analytic_segment_one_id
            self.analytic_segment_two_id = self.reason_code_id.analytic_segment_two_id
