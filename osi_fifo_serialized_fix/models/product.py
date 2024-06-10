from odoo import models
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _run_fifo(self, quantity, company):
        if self.tracking == "none":
            res = super()._run_fifo(quantity, company)
            return res
        rel_stock_move = (
            self._context.get("stock_move_id") or self.env["stock.move"].sudo()
        )

        self.ensure_one()

        # Find back incoming stock valuation layers
        # (called candidates here) to value `quantity`.
        used_candidates = []
        for line in rel_stock_move.move_line_ids:
            quantity = line.quantity
            qty_to_take_on_candidates = quantity
            candidates = (
                self.env["stock.valuation.layer"]
                .sudo()
                .search(
                    [
                        ("product_id", "=", self.id),
                        ("remaining_qty", ">", 0),
                        ("company_id", "=", company.id),
                        ("lot_ids", "in", line.lot_id.id)
                    ]
                )
            )
            new_standard_price = 0
            tmp_value = 0  # to accumulate the value taken on the candidates
            for candidate in candidates:
                if line.lot_id in candidate.lot_ids:
                    qty_taken_on_candidate = min(
                        qty_to_take_on_candidates, candidate.remaining_qty
                    )
                    candidate_unit_cost = (
                        candidate.remaining_value / candidate.remaining_qty
                    )
                    new_standard_price = candidate_unit_cost
                    value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                    value_taken_on_candidate = candidate.currency_id.round(
                        value_taken_on_candidate
                    )
                    new_remaining_value = (
                        candidate.remaining_value - value_taken_on_candidate
                    )

                    candidate_vals = {
                        "remaining_qty": candidate.remaining_qty - qty_taken_on_candidate,
                        "remaining_value": new_remaining_value,
                    }

                    candidate.write(candidate_vals)
                    used_candidates.append(candidate.id)

                    qty_to_take_on_candidates -= qty_taken_on_candidate
                    tmp_value += value_taken_on_candidate
                    candidate.write({"used_price": new_standard_price, "used_tmp_value": tmp_value})
                    if float_is_zero(
                        qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding
                    ):
                        if float_is_zero(
                            candidate.remaining_qty, precision_rounding=self.uom_id.rounding
                        ):
                            next_candidates = candidates.filtered(
                                lambda svl: svl.remaining_qty > 0
                            )
                            new_standard_price = (
                                next_candidates
                                and next_candidates[0].unit_cost
                                or new_standard_price
                            )
                            candidate.write({"used_price": new_standard_price, "used_tmp_value": tmp_value})
                        break

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and self.cost_method == "fifo":
            self.sudo().with_company(company.id).with_context(
                disable_auto_svl=True
            ).standard_price = new_standard_price

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        vals = {}
        if float_is_zero(
            qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding
        ):
            vals = {
                "value": -tmp_value,
                "unit_cost": tmp_value / quantity,
            }
        else:
            assert qty_to_take_on_candidates > 0
            last_fifo_price = new_standard_price or self.standard_price
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            vals = {
                "remaining_qty": -qty_to_take_on_candidates,
                "value": -tmp_value,
                "unit_cost": last_fifo_price,
            }
        vals.update({"used_candidates": used_candidates})
        return vals
