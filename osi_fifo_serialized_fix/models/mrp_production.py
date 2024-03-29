# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_round


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        res = super().button_mark_done()

        # Below code will fix the FIFO SN costing for Raw material, FG and By product
        # recalculate all JE for last MO
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id
            and x.state == "done"
            and x.quantity_done > 0
        )
        consumed_moves = self.move_raw_ids
        if finished_move:
            work_center_cost = 0
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(
                    lambda t: t.date_end and not t.cost_already_recorded
                )
                work_center_cost += work_order._cal_cost(times=time_lines)
                time_lines.write({"cost_already_recorded": True})
            qty_done = finished_move.product_uom._compute_quantity(
                finished_move.quantity_done, finished_move.product_id.uom_id
            )
            extra_cost = self.extra_cost * qty_done
            total_cost = (
                -sum(
                    consumed_moves.sudo()
                    .stock_valuation_layer_ids.filtered(lambda svl: svl.quantity < 0)
                    .mapped("value")
                )
                + work_center_cost
                + extra_cost
            )
            byproduct_moves = self.move_byproduct_ids.filtered(
                lambda m: m.state == "done"
                and m.quantity_done > 0
                and m.cost_share != 0
            )
            byproduct_cost_share = 0
            for byproduct in byproduct_moves:
                byproduct_cost_share += byproduct.cost_share
                if byproduct.product_id.cost_method in ("fifo", "average"):
                    byproduct_svl = byproduct.sudo().stock_valuation_layer_ids
                    byproduct.price_unit = float_round(
                        total_cost
                        * byproduct.cost_share
                        / 100
                        / byproduct.product_uom._compute_quantity(
                            byproduct.quantity_done, byproduct.product_id.uom_id
                        ),
                        precision_rounding=byproduct_svl.currency_id.rounding,
                    )
                    if byproduct.lot_ids:
                        byproduct.lot_ids.write({"real_price": byproduct.price_unit})
                    self._correct_svl_je(byproduct_svl, byproduct, byproduct.price_unit)
            if (
                finished_move.product_id.valuation == "manual_periodic"
                and byproduct_cost_share
            ):
                # If the FG gets no value, ensure the byproducts have the total value
                # Corrects rounding issues too
                total_value_byproducts = sum(byproduct_moves.mapped("price_unit"))
                remainder = float_round(
                    total_cost - total_value_byproducts, precision_rounding=0.0001
                )
                if remainder != 0.0:
                    for byproduct in byproduct_moves.filtered(
                        lambda m: m.product_id.cost_method in ("fifo", "average")
                    ):
                        byproduct.price_unit = byproduct.price_unit + remainder
                        if byproduct.lot_ids:
                            byproduct.lot_ids.write(
                                {"real_price": byproduct.price_unit}
                            )
                        self._correct_svl_je(
                            byproduct.sudo().stock_valuation_layer_ids,
                            byproduct,
                            byproduct.price_unit,
                        )
                        break
            if finished_move.product_id.cost_method in ("fifo", "average"):
                finished_move.price_unit = (
                    total_cost
                    * float_round(
                        1 - byproduct_cost_share / 100, precision_rounding=0.0001
                    )
                    / qty_done
                )
                total_cost = finished_move.price_unit
                self.lot_producing_id.real_price = total_cost
                fg_svl = (
                    finished_move.stock_valuation_layer_ids
                    and finished_move.stock_valuation_layer_ids[0]
                    or []
                )
                self._correct_svl_je(fg_svl, finished_move, total_cost)
        if self.analytic_account_id:
            self.analytic_account_id.line_ids.write({"manufacturing_order_id": self.id})
        return res

    def _correct_svl_je(self, svl, stock_move, total_cost):
        account_move_id = svl.account_move_id
        svl.unit_cost = total_cost / (svl.quantity if svl.quantity > 0 else 1)
        svl.value = svl.unit_cost * svl.quantity
        svl.remaining_value = svl.unit_cost * svl.quantity
        svl.remaining_qty = svl.quantity

        if not account_move_id:
            svl._validate_accounting_entries()
        else:
            # Change the SVl with correct cost
            account_move_id.button_draft()
            # The Valuation Layer has been changed,
            # now we have to edit the STJ Entry
            for ji_id in account_move_id.line_ids:
                if ji_id.credit != 0:
                    ji_id.with_context(check_move_validity=False).write(
                        {"credit": total_cost}
                    )
                else:
                    ji_id.with_context(check_move_validity=False).write(
                        {"debit": total_cost}
                    )
            account_move_id.action_post()
