# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        res_temp = super(AccountInvoice, self)._anglo_saxon_sale_move_lines(
            i_line)
        res = []
        for item in res_temp:
            item['invl_id'] = i_line.id
            res.append(item)
        return res
