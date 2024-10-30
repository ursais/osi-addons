# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_invoice_line_from_rma_line(self, line):
        data = super()._prepare_invoice_line_from_rma_line(line)
        if line.purchase_order_line_id:
            data["purchase_line_id"] = line.purchase_order_line_id.id
        return data

    def action_post(self):
        res = super().action_post()
        for move in self:
            rma_mls = move.line_ids.filtered(lambda x: x.rma_line_id)
            if rma_mls:
                # Try to reconcile the interim accounts for RMA lines
                rmas = rma_mls.mapped("rma_line_id")
                for rma in rmas:
                    product_accounts = (
                        rma.product_id.product_tmpl_id._get_product_accounts()
                    )
                    if rma.type == "customer":
                        product_interim_account = product_accounts["stock_output"]
                    else:
                        product_interim_account = product_accounts["stock_input"]
                    if product_interim_account.reconcile:
                        # Get the in and out moves
                        amls = self.env["account.move.line"].search(
                            [
                                ("rma_line_id", "=", rma.id),
                                ("account_id", "=", product_interim_account.id),
                                ("parent_state", "=", "posted"),
                                ("reconciled", "=", False),
                            ]
                        )
                        amls.reconcile()
        return res

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        lines_vals_list_rma = []
        rma_refunds = self.env["account.move"]
        price_unit_prec = self.env["decimal.precision"].precision_get("Product Price")
        for move in self:
            if (
                move.move_type != "in_refund"
                or not move.company_id.anglo_saxon_accounting
            ):
                continue
            move = move.with_company(move.company_id)
            for line in move.invoice_line_ids.filtered(lambda il: il.rma_line_id):
                # Filter out lines being not eligible for price difference.
                # Moreover, this function is used for standard cost method only.
                if (
                    line.product_id.type != "product"
                    or line.product_id.valuation != "real_time"
                ):
                    continue

                # Retrieve accounts needed to generate the price difference.
                debit_expense_account = line._get_price_diff_account()
                if not debit_expense_account:
                    continue
                # Retrieve stock valuation moves.
                valuation_stock_moves = (
                    self.env["stock.move"].search(
                        [
                            ("rma_line_id", "=", line.rma_line_id.id),
                            ("state", "=", "done"),
                            ("product_qty", "!=", 0.0),
                        ]
                    )
                    if line.rma_line_id
                    else self.env["stock.move"]
                )

                if line.product_id.cost_method != "standard" and line.rma_line_id:
                    if move.move_type == "in_refund":
                        valuation_stock_moves = valuation_stock_moves.filtered(
                            lambda stock_move: stock_move._is_out()
                        )
                    else:
                        valuation_stock_moves = valuation_stock_moves.filtered(
                            lambda stock_move: stock_move._is_in()
                        )

                    if not valuation_stock_moves:
                        continue

                    (
                        valuation_price_unit_total,
                        valuation_total_qty,
                    ) = valuation_stock_moves._get_valuation_price_and_qty(
                        line, move.currency_id
                    )
                    valuation_price_unit = (
                        valuation_price_unit_total / valuation_total_qty
                    )
                    valuation_price_unit = line.product_id.uom_id._compute_price(
                        valuation_price_unit, line.product_uom_id
                    )
                else:
                    # Valuation_price unit is always expressed in invoice currency,
                    # so that it can always be computed with the good rate
                    price_unit = line.product_id.uom_id._compute_price(
                        line.product_id.standard_price, line.product_uom_id
                    )
                    price_unit = (
                        -price_unit
                        if line.move_id.move_type == "in_refund"
                        else price_unit
                    )
                    valuation_date = (
                        valuation_stock_moves
                        and max(valuation_stock_moves.mapped("date"))
                        or move.date
                    )
                    valuation_price_unit = line.company_currency_id._convert(
                        price_unit,
                        move.currency_id,
                        move.company_id,
                        valuation_date,
                        round=False,
                    )

                price_unit = line._get_gross_unit_price()

                price_unit_val_dif = abs(price_unit) - valuation_price_unit
                relevant_qty = line.quantity
                price_subtotal = relevant_qty * price_unit_val_dif
                # We consider there is a price difference if the subtotal is not zero.
                # In case a discount has been applied, we can't round the price unit
                # anymore, and hence we can't compare them.
                if (
                    not move.currency_id.is_zero(price_subtotal)
                    and float_compare(
                        line["price_unit"],
                        line.price_unit,
                        precision_digits=price_unit_prec,
                    )
                    == 0
                ):
                    # Add price difference account line.
                    vals = {
                        "name": line.name[:64],
                        "move_id": move.id,
                        "partner_id": line.partner_id.id
                        or move.commercial_partner_id.id,
                        "currency_id": line.currency_id.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "quantity": relevant_qty,
                        "price_unit": price_unit_val_dif,
                        "price_subtotal": relevant_qty * price_unit_val_dif,
                        "amount_currency": relevant_qty
                        * price_unit_val_dif
                        * line.move_id.direction_sign,
                        "balance": line.currency_id._convert(
                            relevant_qty
                            * price_unit_val_dif
                            * line.move_id.direction_sign,
                            line.company_currency_id,
                            line.company_id,
                            fields.Date.today(),
                        ),
                        "account_id": debit_expense_account.id,
                        "analytic_distribution": line.analytic_distribution,
                        "display_type": "cogs",
                        "rma_line_id": line.rma_line_id.id,
                    }

                    lines_vals_list_rma.append(vals)

                    # Correct the amount of the current line.
                    vals = {
                        "name": line.name[:64],
                        "move_id": move.id,
                        "partner_id": line.partner_id.id
                        or move.commercial_partner_id.id,
                        "currency_id": line.currency_id.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "quantity": relevant_qty,
                        "price_unit": -price_unit_val_dif,
                        "price_subtotal": relevant_qty * -price_unit_val_dif,
                        "amount_currency": relevant_qty
                        * -price_unit_val_dif
                        * line.move_id.direction_sign,
                        "balance": line.currency_id._convert(
                            relevant_qty
                            * -price_unit_val_dif
                            * line.move_id.direction_sign,
                            line.company_currency_id,
                            line.company_id,
                            fields.Date.today(),
                        ),
                        "account_id": line.account_id.id,
                        "analytic_distribution": line.analytic_distribution,
                        "display_type": "cogs",
                        "rma_line_id": line.rma_line_id.id,
                    }
                    lines_vals_list_rma.append(vals)
                    rma_refunds |= move
        lines_vals_list = super(
            AccountMove, self - rma_refunds
        )._stock_account_prepare_anglo_saxon_in_lines_vals()
        lines_vals_list += lines_vals_list_rma
        return lines_vals_list
