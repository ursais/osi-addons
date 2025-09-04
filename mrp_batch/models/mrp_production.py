# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError
from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, Command
from odoo.addons.web.controllers.utils import clean_action
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby, topological_sort

class MrpProduction(models.Model):
    """Inherit Manufacturing Orders to add Batch Functionality."""

    _inherit = "mrp.production"

    # COLUMNS #########

    mrp_batch_id = fields.Many2one(
        "mrp.production.batch",
        string="MRP Batch",
        domain="[('state', 'not in', ('done','cancel','hold'))]",
        copy=False,
    )
    mrp_batch_state = fields.Selection(
        related="mrp_batch_id.state",
        readonly=True,
        string="Batch Status",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
    )
    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
    )
    sale_state = fields.Selection(
        related="sale_order_id.state",
        store=True,
    )
    linked_mo_ids = fields.Many2many(
                comodel_name="mrp.production",
                string="Linked MO",
                relation="rel_mrp_production_group",
                column1="mo_id",
                column2="linked_mo_id",
            )



    def button_plan(self):
        """
        Override button_plan to generate a serial number if
        the product is serialized
        """
        res = super().button_plan()

        for order in self:
            if order.product_id.tracking == "serial" and not order.lot_producing_id:
                # Generate serial number for the finished product during plan
                if order.product_id.tracking == "serial":
                    lot = self.env["stock.lot"].create(
                        {
                            "name": self.env["ir.sequence"].next_by_code(
                                "stock.lot.serial"
                            )
                            or "/",
                            "product_id": order.product_id.id,
                            "company_id": order.company_id.id,
                        }
                    )
                    order.lot_producing_id = lot.id

        return res

    def action_remove_batch(self):
        if self.filtered(lambda batch: not batch.mrp_batch_id):
            raise UserError(
                "No batch found to remove or batch has already been removed."
            )
        if self.mapped("mrp_batch_id").filtered(
            lambda batch: batch.state in ("done", "cancel", "hold")
        ):
            raise UserError("Some manufacting Batch you can't removed.")
        self.mrp_batch_id = False

    def action_open_wizard(self):
        # Check if any record already has an assigned batch
        if any(record.mrp_batch_id for record in self):
            raise UserError(
                "A batch has already been created for one or more selected records."
            )

        # Check for records in 'done' or 'cancel' state
        if any(record.state in ["done", "cancel"] for record in self):
            raise UserError(
                "You cannot create a batch for records that are in 'Done' or 'Cancel' state."
            )

        # Return the action only after all checks are completed
        return {
            "name": "Create Batch",
            "type": "ir.actions.act_window",
            "res_model": "mrp.production.batch.wizard",
            "view_mode": "form",
            "target": "new",
        }

    @api.depends(
        "move_raw_ids.state",
        "move_raw_ids.quantity",
        "move_finished_ids.state",
        "workorder_ids.state",
        "product_qty",
        "qty_producing",
        "move_raw_ids.picked",
    )
    def _compute_state(self):
        # Call the original compute logic
        res = super()._compute_state()

        # Trigger batch state computation for related batches
        for production in self:
            if production.mrp_batch_id:
                production.mrp_batch_id._compute_batch_state()

        return res

    def _split_productions(self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False):
        """ Splits productions into productions smaller quantities to produce, i.e. creates
        its backorders.

        :param dict amounts: a dict with a production as key and a list value containing
        the amounts each production split should produce including the original production,
        e.g. {mrp.production(1,): [3, 2]} will result in mrp.production(1,) having a product_qty=3
        and a new backorder with product_qty=2.
        :param bool cancel_remaining_qty: whether to cancel remaining quantities or generate
        an additional backorder, e.g. having product_qty=5 if mrp.production(1,) product_qty was 10.
        :param bool set_consumed_qty: whether to set quantity on move lines to the reserved quantity
        or the initial demand if no reservation, except for the remaining backorder.
        :return: mrp.production records in order of [orig_prod_1, backorder_prod_1,
        backorder_prod_2, orig_prod_2, backorder_prod_2, etc.]
        """
        def _default_amounts(production):
            return [production.qty_producing, production._get_quantity_to_backorder()]

        if not amounts:
            amounts = {}
        has_backorder_to_ignore = defaultdict(lambda: False)
        for production in self:
            mo_amounts = amounts.get(production)
            if not mo_amounts:
                amounts[production] = _default_amounts(production)
                continue
            total_amount = sum(mo_amounts)
            diff = float_compare(production.product_qty, total_amount, precision_rounding=production.product_uom_id.rounding)
            if diff > 0 and not cancel_remaining_qty:
                amounts[production].append(production.product_qty - total_amount)
                has_backorder_to_ignore[production] = True
            elif not self.env.context.get('allow_more') and (diff < 0 or production.state in ['done', 'cancel']):
                raise UserError(_("Unable to split with more than the quantity to produce."))

        backorder_vals_list = []
        initial_qty_by_production = {}

        # Create the backorders.
        for production in self:
            mo_name = production.name
            initial_qty_by_production[production] = production.product_qty
            if production.backorder_sequence == 0:  # Activate backorder naming
                production.backorder_sequence = 1
            production.name = self._get_name_backorder(production.name, production.backorder_sequence)
            (production.move_raw_ids | production.move_finished_ids).name = production.name
            (production.move_raw_ids | production.move_finished_ids).origin = production._get_origin()
            backorder_vals = production.copy_data(default=production._get_backorder_mo_vals())[0]
            backorder_qtys = amounts[production][1:]
            production.with_context(skip_compute_move_raw_ids=True).product_qty = amounts[production][0]

            next_seq = max(production.procurement_group_id.mrp_production_ids.mapped("backorder_sequence"), default=1)

            # OSI Customisation start
            i = 1
            for qty_to_backorder in backorder_qtys:
                next_seq += 1
                procurement_group = self.env['procurement.group'].create({
                    'name': f'{mo_name}-{i+1}',
                })
                backorder_vals['procurement_group_id'] = procurement_group.id
                backorder_vals_list.append(dict(
                    backorder_vals,
                    product_qty=qty_to_backorder,
                    name=production._get_name_backorder(production.name, next_seq),
                    backorder_sequence=next_seq
                ))
                i+=1

            # OSI Customisation end

        backorders = self.env['mrp.production'].with_context(skip_confirm=True).create(backorder_vals_list)

        index = 0
        production_to_backorders = {}
        production_ids = OrderedSet()
        for production in self:
            number_of_backorder_created = len(amounts.get(production, _default_amounts(production))) - 1
            production_backorders = backorders[index:index + number_of_backorder_created]
            production_to_backorders[production] = production_backorders
            production_ids.update(production.ids)
            production_ids.update(production_backorders.ids)
            index += number_of_backorder_created

        # Split the `stock.move` among new backorders.
        new_moves_vals = []
        moves = []
        move_to_backorder_moves = {}
        # unlink all unregistered move lines linked a move containing an effictive registration
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda m: m.picked and not m.additional).move_line_ids.filtered(lambda ml: not ml.picked).unlink()
        for production in self:
            for move in production.move_raw_ids | production.move_finished_ids:
                if move.additional:
                    continue
                move_to_backorder_moves[move] = self.env['stock.move']
                unit_factor = move.product_uom_qty / initial_qty_by_production[production]
                initial_move_vals = move.copy_data(move._get_backorder_move_vals())[0]
                move.with_context(do_not_unreserve=True, no_procurement=True).product_uom_qty = production.product_qty * unit_factor

                for backorder in production_to_backorders[production]:
                    move_vals = dict(
                        initial_move_vals,
                        product_uom_qty=backorder.product_qty * unit_factor
                    )
                    if move.raw_material_production_id:
                        move_vals['raw_material_production_id'] = backorder.id
                    else:
                        move_vals['production_id'] = backorder.id
                    new_moves_vals.append(move_vals)
                    moves.append(move)

        backorder_moves = self.env['stock.move'].create(new_moves_vals)
        move_to_assign = backorder_moves
        # Split `stock.move.line`s. 2 options for this:
        # - do_unreserve -> action_assign
        # - Split the reserved amounts manually
        # The first option would be easier to maintain since it's less code
        # However it could be slower (due to `stock.quant` update) and could
        # create inconsistencies in mass production if a new lot higher in a
        # FIFO strategy arrives between the reservation and the backorder creation
        for move, backorder_move in zip(moves, backorder_moves):
            move_to_backorder_moves[move] |= backorder_move

        move_lines_vals = []
        assigned_moves = set()
        partially_assigned_moves = set()
        move_lines_to_unlink = set()
        moves_to_consume = self.env['stock.move']
        for initial_move, backorder_moves in move_to_backorder_moves.items():
            # Create `stock.move.line` for consumed but non-reserved components and for by-products
            if set_consumed_qty and (initial_move.raw_material_production_id or (initial_move.production_id and initial_move.product_id != production.product_id)):
                ml_vals = initial_move._prepare_move_line_vals()
                backorder_move_to_ignore = backorder_moves[-1] if has_backorder_to_ignore[initial_move.raw_material_production_id] else self.env['stock.move']
                for move in (initial_move + backorder_moves - backorder_move_to_ignore):
                    if not initial_move.move_line_ids:
                        new_ml_vals = dict(
                            ml_vals,
                            quantity=move.product_uom_qty,
                            move_id=move.id
                        )
                        move_lines_vals.append(new_ml_vals)
                    moves_to_consume |= move

        for initial_move, backorder_moves in move_to_backorder_moves.items():
            ml_by_move = []
            product_uom = initial_move.product_id.uom_id
            if not initial_move.picked:
                for move_line in initial_move.move_line_ids.sorted(key=lambda ml: ml._sorting_move_lines()):
                    available_qty = move_line.product_uom_id._compute_quantity(move_line.quantity, product_uom, rounding_method="HALF-UP")
                    if float_compare(available_qty, 0, precision_rounding=product_uom.rounding) <= 0:
                        continue
                    ml_by_move.append((available_qty, move_line, move_line.copy_data()[0]))

            moves = list(initial_move | backorder_moves)

            move = moves and moves.pop(0)
            move_qty_to_reserve = move.product_qty  # Product UoM

            for index, (quantity, move_line, ml_vals) in enumerate(ml_by_move):
                taken_qty = min(quantity, move_qty_to_reserve)
                taken_qty_uom = product_uom._compute_quantity(taken_qty, move_line.product_uom_id, rounding_method="HALF-UP")
                if float_is_zero(taken_qty_uom, precision_rounding=move_line.product_uom_id.rounding):
                    continue
                move_line.write({
                    'quantity': taken_qty_uom,
                    'move_id': move.id,
                })
                move_qty_to_reserve -= taken_qty
                ml_by_move[index] = (quantity - taken_qty, move_line, ml_vals)

                if float_compare(move_qty_to_reserve, 0, precision_rounding=move.product_uom.rounding) <= 0:
                    assigned_moves.add(move.id)
                    move = moves and moves.pop(0)
                    move_qty_to_reserve = move and move.product_qty or 0

            for quantity, move_line, ml_vals in ml_by_move:
                while float_compare(quantity, 0, precision_rounding=product_uom.rounding) > 0 and move:
                    # Do not create `stock.move.line` if there is no initial demand on `stock.move`
                    taken_qty = min(move_qty_to_reserve, quantity)
                    taken_qty_uom = product_uom._compute_quantity(taken_qty, move_line.product_uom_id, rounding_method="HALF-UP")
                    if move == initial_move:
                        move_line.quantity += taken_qty_uom
                    elif not float_is_zero(taken_qty_uom, precision_rounding=move_line.product_uom_id.rounding):
                        new_ml_vals = dict(
                            ml_vals,
                            quantity=taken_qty_uom,
                            move_id=move.id
                        )
                        move_lines_vals.append(new_ml_vals)
                    quantity -= taken_qty
                    move_qty_to_reserve -= taken_qty

                    if float_compare(move_qty_to_reserve, 0, precision_rounding=move.product_uom.rounding) <= 0:
                        assigned_moves.add(move.id)
                        move = moves and moves.pop(0)
                        move_qty_to_reserve = move and move.product_qty or 0

            if move and move_qty_to_reserve != move.product_qty:
                partially_assigned_moves.add(move.id)

            move_lines_to_unlink.update(initial_move.move_line_ids.filtered(lambda ml: not ml.quantity).ids)

        # reserve new backorder moves depending on the picking type
        self.env['stock.move'].browse(assigned_moves).write({'state': 'assigned'})
        self.env['stock.move'].browse(partially_assigned_moves).write({'state': 'partially_available'})
        self.env['stock.move.line'].create(move_lines_vals)
        move_to_assign = move_to_assign.filtered(
            lambda move: move.state in ('confirmed', 'partially_available')
            and (move._should_bypass_reservation()
                or move.picking_type_id.reservation_method == 'at_confirm'
                or (move.reservation_date and move.reservation_date <= fields.Date.today())))
        move_to_assign._action_assign()

        # Avoid triggering a useless _recompute_state
        self.env['stock.move.line'].browse(move_lines_to_unlink).write({'move_id': False})
        self.env['stock.move.line'].browse(move_lines_to_unlink).unlink()

        moves_to_consume.write({'picked': True})

        workorders_to_cancel = self.env['mrp.workorder']
        for production in self:
            initial_qty = initial_qty_by_production[production]
            initial_workorder_remaining_qty = []
            bo = production_to_backorders[production]

            # Adapt duration
            for workorder in bo.workorder_ids:
                workorder.duration_expected = workorder._get_duration_expected()

            # Adapt quantities produced
            for workorder in production.workorder_ids.sorted('id'):
                initial_workorder_remaining_qty.append(max(initial_qty - workorder.qty_reported_from_previous_wo - workorder.qty_produced, 0))
                if workorder.production_id.id not in (self.env.context.get('mo_ids_to_backorder') or []):
                    workorder.qty_produced = min(workorder.qty_produced, workorder.qty_production)
            workorders_len = len(production.workorder_ids)
            for index, workorder in enumerate(bo.workorder_ids):
                remaining_qty = initial_workorder_remaining_qty[index % workorders_len]
                workorder.qty_reported_from_previous_wo = max(workorder.qty_production - remaining_qty, 0)
                if remaining_qty:
                    initial_workorder_remaining_qty[index % workorders_len] = max(remaining_qty - workorder.qty_produced, 0)
                else:
                    workorders_to_cancel += workorder
        workorders_to_cancel.action_cancel()
        backorders._action_confirm_mo_backorders()

        return self.env['mrp.production'].browse(production_ids)
    # END #########
