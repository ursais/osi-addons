# Copyright (C) 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _run_fifo(self, move, quantity=None):

        if move.product_id.tracking == "none":
            res = super()._run_fifo(move, quantity)
        else:
            valued_move_lines = move.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
            new_standard_price = 0
            tmp_qty = 0
            tmp_value = 0
            candidates = move.product_id._get_fifo_candidates_in_move_with_company(move.company_id.id)
            for valued_move_line in valued_move_lines:
                valued_quantity = 0
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
                # Find back incoming stock moves (called candidates here) to value this move.
                qty_to_take_on_candidates = quantity or valued_quantity
                for candidate in candidates:
                    # Check if the lot_id of the move line matches any lot_id for the candidate lines.
                    allowed_canditates_lines = self.env["stock.move.line"].search([("move_id", "=", candidate.id),("lot_id", "=", valued_move_line.lot_id.id)])
                    if allowed_canditates_lines:
                        new_standard_price = candidate.price_unit
                        if candidate.remaining_qty <= qty_to_take_on_candidates:
                            qty_taken_on_candidate = candidate.remaining_qty
                        else:
                            qty_taken_on_candidate = qty_to_take_on_candidates
                        candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
                        value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
                        candidate_vals = {
                            "remaining_qty": candidate.remaining_qty - qty_taken_on_candidate,
                            "remaining_value": candidate.remaining_value - value_taken_on_candidate,
                        }
                        candidate.write(candidate_vals)

                        qty_to_take_on_candidates -= qty_taken_on_candidate
                        tmp_qty += qty_taken_on_candidate
                        tmp_value += value_taken_on_candidate
                        if qty_to_take_on_candidates == 0:
                            break
            # Update the standard price with the price of the last used candidate, if any.
            if new_standard_price and move.product_id.cost_method == "fifo":
                move.product_id.sudo().with_context(force_company=move.company_id.id) \
                    .standard_price = new_standard_price
            # If there's still quantity to value but we're out of candidates, we fall in the
            # negative stock use case. We chose to value the out move at the price of the
            # last out and a correction entry will be made once `_fifo_vacuum` is called.
            if qty_to_take_on_candidates == 0:
                # If the move is not valued yet we compute the price_unit based on the value taken on
                # the candidates.
                # If the move has already been valued, it means that we editing the qty_done on the
                # move. In this case, the price_unit computation should take into account the quantity
                # already valued and the new quantity taken.
                if not move.value:
                    price_unit = -tmp_value / (move.product_qty or quantity)
                else:
                    price_unit = (-(tmp_value) + move.value) / (tmp_qty + move.product_qty)
                move.write({
                    "value": -tmp_value if not quantity else move.value or -tmp_value,  # outgoing move are valued negatively
                    "price_unit": price_unit,
                })
            elif qty_to_take_on_candidates > 0:
                last_fifo_price = new_standard_price or move.product_id.standard_price
                negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
                tmp_value += abs(negative_stock_value)
                vals = {
                    "remaining_qty": move.remaining_qty + -qty_to_take_on_candidates,
                    "remaining_value": move.remaining_value + negative_stock_value,
                    "value": -tmp_value,
                    "price_unit": -1 * last_fifo_price,
                }
                move.write(vals)
            res = tmp_value
        return res
