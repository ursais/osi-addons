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
        enable_split = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_so_action_confirm")
            )
        if enable_split == "True":
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
                    if qty > 1:
                        # Perform the split and get new MOs
                        new_mos = mo.sudo()._split_productions({mo: ([1])})[
                            :-1
                        ]
                        # Assign the batch to newly created MOs
                        for new_mo in new_mos:
                            new_mo.write(
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

                    # Assign batch to original MO and its backorders
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
