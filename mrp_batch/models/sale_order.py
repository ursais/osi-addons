# Import Odoo libs
from odoo import fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # COLUMNS #########

    mrp_batch_count = fields.Integer(
        string="mrp batch count",
        compute="_compute_mrp_production_batch_id_count",
    )
    is_mrp_warning = fields.Boolean(compute="_compute_is_mrp_warning")

    # END #########
    # METHODS #####

    def write(self, vals):
        res = super().write(vals)
        if vals.get("order_line", False):
            self.with_delay().split_mo()
        return res

    def _compute_is_mrp_warning(self):
        for so in self:
            is_mrp_warning = False

            # Check if there are any related manufacturing orders (mrp_production_ids)
            # and if any of those orders are planned or in specific states
            if so.mrp_production_ids and so.mrp_production_ids.filtered(
                lambda l: l.is_planned or l.state in ("progress", "to_close", "done")
            ):
                is_mrp_warning = True

            so.is_mrp_warning = is_mrp_warning

    def action_confirm(self):
        # Calls the original `action_confirm` method from the super class to
        # confirm the record.
        res = super().action_confirm()
        # Asynchronously triggers the `split_mo` method to split
        # manufacturing orders (MOs).
        self.with_delay().split_mo()
        return res

    def split_mo(self):
        batch_obj = self.env["mrp.production.batch"]
        batch_mode = (
            self.env["ir.config_parameter"].sudo().get_param("mrp_batch.batch_mode")
        )

        for rec in self:
            existing_batch_id = None

            if batch_mode == "single":
                existing_batch_id = batch_obj.create(
                    {"responsible_id": rec.env.user.id}
                )

            for mo in rec.mrp_production_ids:
                if (
                    mo.product_id.tracking == "serial"
                    and mo.product_id.is_allow_split_mo
                ):
                    qty = mo.product_qty
                    if qty > 1:
                        # Store original pickings BEFORE split
                        original_pickings = mo.picking_ids.filtered(
                            lambda p: p.state not in ["done", "cancel"]
                        )

                        # Split into MOs
                        new_mos = mo.sudo()._split_productions({mo: [1] * int(qty)})[
                            :-1
                        ]

                        for new_mo in new_mos:
                            new_batch_id = (
                                existing_batch_id.id
                                if batch_mode == "single"
                                else batch_obj.create(
                                    {"responsible_id": rec.env.user.id}
                                ).id
                            )
                            new_mo.write({"mrp_batch_id": new_batch_id})

                            # --- Split picking for this MO ---
                            for picking in original_pickings:
                                # Create new picking
                                new_picking = picking.copy(
                                    {
                                        "origin": new_mo.name,
                                        "group_id": new_mo.procurement_group_id.id,
                                        "move_ids": [],
                                        "move_ids_without_package": False,
                                    }
                                )

                                for move in picking.move_ids:
                                    # Use the ratio of original qty to determine component qty
                                    if not move.product_uom_qty or not mo.product_qty:
                                        continue

                                    per_unit_qty = move.product_uom_qty / mo.product_qty

                                    new_move = self.env["stock.move"].create(
                                        {
                                            "name": move.name,
                                            "product_id": move.product_id.id,
                                            "product_uom": move.product_uom.id,
                                            "product_uom_qty": per_unit_qty,
                                            "picking_id": new_picking.id,
                                            "location_id": move.location_id.id,
                                            "location_dest_id": move.location_dest_id.id,
                                            "raw_material_production_id": new_mo.id,
                                            "state": "draft",
                                        }
                                    )

                                new_picking.action_confirm()
                                new_picking.action_assign()

                                # Add to stock picking batch
                                batch = self.env["stock.picking.batch"].search(
                                    [
                                        (
                                            "picking_type_id",
                                            "=",
                                            new_picking.picking_type_id.id,
                                        ),
                                        ("state", "=", "draft"),
                                    ],
                                    limit=1,
                                )
                                if not batch:
                                    batch = self.env["stock.picking.batch"].create(
                                        {
                                            "picking_type_id": new_picking.picking_type_id.id,
                                        }
                                    )
                                batch.picking_ids = [(4, new_picking.id)]

                    # Assign batch to original MO and backorders
                    mo.write(
                        {
                            "mrp_batch_id": (
                                existing_batch_id.id
                                if batch_mode == "single"
                                else batch_obj.create(
                                    {"responsible_id": rec.env.user.id}
                                ).id
                            )
                        }
                    )
                    mo.backorder_ids.write({"mrp_batch_id": mo.mrp_batch_id.id})

    # def split_mo(self):
    #     batch_obj = self.env["mrp.production.batch"]
    #     batch_mode = (
    #         self.env["ir.config_parameter"].sudo().get_param("mrp_batch.batch_mode")
    #     )

    #     for rec in self:
    #         existing_batch_id = None

    #         if batch_mode == "single":
    #             # Create a single batch for all MOs in this record
    #             existing_batch_id = batch_obj.create(
    #                 {"responsible_id": rec.env.user.id}
    #             )

    #         for mo in rec.mrp_production_ids:
    #             if (
    #                 mo.product_id.tracking == "serial"
    #                 and mo.product_id.is_allow_split_mo
    #             ):
    #                 qty = mo.product_qty
    #                 if qty > 1:
    #                     # Perform the split and get new MOs
    #                     new_mos = mo.sudo()._split_productions({mo: ([1] * int(qty))})[
    #                         :-1
    #                     ]

    #                     # Assign the batch to newly created MOs
    #                     for new_mo in new_mos:
    #                         new_mo.write(
    #                             {
    #                                 "mrp_batch_id": (
    #                                     existing_batch_id.id
    #                                     if batch_mode == "single"
    #                                     else batch_obj.create(
    #                                         {"responsible_id": rec.env.user.id}
    #                                     ).id
    #                                 )
    #                             }
    #                         )

    #                 # Assign batch to original MO and its backorders
    #                 mo.write(
    #                     {
    #                         "mrp_batch_id": (
    #                             existing_batch_id.id
    #                             if batch_mode == "single"
    #                             else batch_obj.create(
    #                                 {"responsible_id": rec.env.user.id}
    #                             ).id
    #                         )
    #                     }
    #                 )
    #                 mo.backorder_ids.write({"mrp_batch_id": mo.mrp_batch_id.id})

    # Methods for Batch Smart Button
    def _compute_mrp_production_batch_id_count(self):
        # Computes the count of unique batch IDs linked to the
        # MOs in `mrp_production_ids`.
        for record in self:
            # Collects batch IDs for each MO in `mrp_production_ids`.
            batch_id = [batch.id for batch in record.mrp_production_ids.mrp_batch_id]
            # Sets `mrp_batch_count` to the number of unique batches found.
            record.mrp_batch_count = len(batch_id)

    def action_view_mrp_production_batch(self):
        # Ensures the method is called on a single record.
        self.ensure_one()
        # Defines the base action for viewing the manufacturing production batch.
        action = {
            "res_model": "mrp.production.batch",
            "type": "ir.actions.act_window",
        }
        # Checks if there is only one batch ID in `mrp_production_ids`.
        if len([batch.id for batch in self.mrp_production_ids.mrp_batch_id]) == 1:
            # If there is a single batch, open it in form view.
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.mrp_production_ids.mrp_batch_id.id,
                }
            )
        else:
            # If there are multiple batches, open them in tree and form view with a
            # domain filter.
            action.update(
                {
                    "name": _(
                        "Manufacturing Production Batch Generated by %s", self.name
                    ),
                    "domain": [("id", "in", self.mrp_production_ids.mrp_batch_id.ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    # END #########
