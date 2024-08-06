# Copyright 2017-22 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        for line in res:
            if (
                line[2]["account_id"]
                != self.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                line[2]["rma_line_id"] = self.rma_line_id.id
        return res

    def _account_entry_move(self, qty, description, svl_id, cost):
        res = super()._account_entry_move(qty, description, svl_id, cost)
        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting
            # entries on the stock interim accounts
            self.rma_line_id._stock_account_anglo_saxon_reconcile_valuation()
            self.rma_line_id._check_refund_zero_cost()
        return res
