# Copyright 2017-22 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    def _validate_accounting_entries(self):
        res = super()._validate_accounting_entries()
        for svl in self:
            # Eventually reconcile together the stock interim accounts
            if svl.company_id.anglo_saxon_accounting:
                svl.stock_move_id.rma_line_id._stock_account_anglo_saxon_reconcile_valuation()
        return res
