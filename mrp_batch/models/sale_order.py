# Import Odoo libs
from odoo import fields, models, _, api


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

    def action_confirm(self):
        res = super().action_confirm()
        if self.mrp_production_ids:
            # This is a patch for workaround of split MO with split transfers
            # Due to execptions MO's are not getting confirmed
            self.mrp_production_ids.write({"ignore_exception": True})
            self.mrp_production_ids.action_confirm()
            self.mrp_production_ids.write({"ignore_exception": False})
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

    @api.depends(
        "procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids"
    )
    def _compute_mrp_production_ids(self):
        res = super()._compute_mrp_production_ids()
        data = self.env["procurement.group"]._read_group(
            [("sale_id", "in", self.ids)], ["sale_id"], ["id:recordset"]
        )
        mrp_productions = {}
        for sale, procurement_groups in data:
            mrp_productions[sale.id] = (
                procurement_groups.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids
                | procurement_groups.mrp_production_ids
                | procurement_groups.stock_move_ids.created_production_id.linked_mo_ids
            )
        for sale in self:
            mrp_production_ids = mrp_productions.get(
                sale.id, self.env["mrp.production"]
            )
            sale.mrp_production_count = len(mrp_production_ids)
            sale.mrp_production_ids = mrp_production_ids
        return res

    def split_mo(self, split_internal_picking=False):
        batch_obj = self.env["mrp.production.batch"]
        batch_mode = (
            self.env["ir.config_parameter"].sudo().get_param("mrp_batch.batch_mode")
        )
        for rec in self:
            existing_batch_id = None

            if batch_mode == "single":
                # Create a single batch for all MOs in this record
                existing_batch_id = batch_obj.create(
                    {"responsible_id": rec.env.user.id}
                )
            for mo in rec.mrp_production_ids:
                if (
                    mo.product_id.tracking == "serial"
                    and mo.product_id.is_allow_split_mo
                ):
                    qty = mo.product_qty
                    new_mos = []
                    mo_to_split = mo
                    for i in range(
                        int(mo_to_split.product_qty) - 1
                    ):  # i.g Split 2 times to end up with 3 MOs
                        # Always split 1 qty from the current MO
                        result = mo_to_split.sudo()._split_productions(
                            {mo_to_split: [1]},
                            split_internal_picking=split_internal_picking,
                        )

                        # result[-1] is the remaining MO, result[0] is the new one
                        new_mo = result[0]
                        mo_to_split = result[
                            -1
                        ]  # Continue splitting from the remaining part
                        new_mos.append(new_mo)

                    # At the end, new_mos has 2 new MOs, and mo_to_split is the last remaining 1-qty MO
                    new_mos.append(mo_to_split)
                    for new_mo in new_mos:
                        mo.write({"linked_mo_ids": [(4, new_mo.id)]})

                    # Assign batch to original MO and its backorders
                    if not mo.mrp_batch_id:
                        mo.write(
                            {
                                "mrp_batch_id": (
                                    existing_batch_id.id
                                    if batch_mode == "single"
                                    else batch_obj.create(
                                        {"responsible_id": rec.env.user.id}
                                    ).id
                                ),
                                "ignore_exception": False,
                            }
                        )
                        mo.backorder_ids.write({"mrp_batch_id": mo.mrp_batch_id.id})
                        mo.linked_mo_ids.filtered(lambda l: not l.mrp_batch_id).write(
                            {
                                "mrp_batch_id": mo.mrp_batch_id.id,
                                "ignore_exception": False,
                            }
                        )

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
