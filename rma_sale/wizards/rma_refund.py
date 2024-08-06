# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models


class RmaRefund(models.TransientModel):
    _inherit = "rma.refund"

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        res = super()._prepare_item(line)
        res["sale_line_id"] = line.sale_line_id.id
        return res

    def _get_refund_price_unit(self, rma):
        price_unit = super()._get_refund_price_unit(rma)
        if rma.operation_id.refund_free_of_charge:
            return price_unit
        if rma.type == "customer":
            if rma.account_move_line_id:
                price_unit = rma.account_move_line_id.price_unit
            elif rma.sale_line_id:
                price_unit = rma.sale_line_id.price_unit
            else:
                # Fall back to the sale price if no reference is found.
                price_unit = rma.product_id.with_company(rma.company_id).lst_price
        return price_unit

    def _get_refund_currency(self, rma):
        currency = rma.currency_id
        if rma.type == "customer":
            if rma.account_move_line_id:
                currency = rma.account_move_line_id.currency_id
            elif rma.sale_line_id:
                currency = rma.sale_line_id.currency_id
            else:
                currency = rma.company_id.currency_id
        return currency


class RmaRefundItem(models.TransientModel):
    _inherit = "rma.refund.item"

    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line", string="Sale Order Line"
    )
