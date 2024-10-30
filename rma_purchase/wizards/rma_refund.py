# Copyright 22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class RmaRefund(models.TransientModel):
    _inherit = "rma.refund"

    def _get_refund_price_unit(self, rma):
        price_unit = super()._get_refund_price_unit(rma)
        if rma.type == "supplier":
            if rma.account_move_line_id:
                price_unit = rma.account_move_line_id.price_unit
            elif rma.purchase_order_line_id:
                price_unit = rma.purchase_order_line_id.price_unit
        return price_unit

    def _get_refund_currency(self, rma):
        currency = super()._get_refund_currency(rma)
        if rma.type == "supplier":
            if rma.account_move_line_id:
                currency = rma.account_move_line_id.currency_id
            elif rma.purchase_order_line_id:
                currency = rma.purchase_order_line_id.currency_id
        return currency
