from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_cost_based_transfer = fields.Boolean(copy=False)
    orig_dest_location_id = fields.Many2one("stock.location", copy=False)
    new_picking_id = fields.Many2one("stock.picking")

    @api.onchange("is_cost_based_transfer")
    def _onchange_cost_based_transfer(self):
        if self.is_cost_based_transfer:
            self.location_dest_id = self.env.ref("stock.stock_location_inter_wh").id
            self.move_ids.location_dest_id = self.env.ref(
                "stock.stock_location_inter_wh"
            ).id

    def copy_move_date(self, picking, new_picking_id):
        move_obj = self.env["stock.move"]
        for move in picking.move_ids:
            move_id = move.copy_data(
                {
                    "picking_id": new_picking_id.id,
                    "location_dest_id": new_picking_id.location_dest_id.id,
                    "location_id": new_picking_id.location_id.id,
                    "picked": True,
                }
            )
            move_ids = move_obj.create(move_id)
            move_ids["move_line_ids"] = [
                (
                    0,
                    0,
                    line.copy_data(
                        {
                            "move_id": False,
                            "location_dest_id": new_picking_id.location_dest_id.id,
                            "location_id": new_picking_id.location_id.id,
                            "picking_id": new_picking_id.id,
                            "quantity": line.quantity,
                        }
                    )[0],
                )
                for line in move.move_line_ids
            ]

    def _action_done(self):
        res = super()._action_done()
        # Create a new picking and update locations for 'Cost based transfer'.
        if not self._context.get("skip_cost_based_transfer"):
            for picking in self.filtered(
                lambda p: p.is_cost_based_transfer and p.picking_type_code == "internal"
            ):
                new_in_picking = picking.copy({"move_ids": False})
                new_in_picking.location_dest_id = picking.orig_dest_location_id
                picking.new_picking_id = new_in_picking.id

                new_in_picking.location_id = self.env.ref(
                    "stock.stock_location_inter_wh"
                ).id
                self.copy_move_date(picking, new_in_picking)
                new_in_picking.action_confirm()
                new_in_picking.with_context(
                    skip_cost_based_transfer=1,
                    button_validate_picking_ids=new_in_picking.ids,
                ).button_validate()
        return res

    def view_new_picking(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        form_view = [(self.env.ref("stock.view_picking_form").id, "form")]
        if "views" in action:
            action["views"] = form_view + [
                (state, view) for state, view in action["views"] if view != "form"
            ]
        else:
            action["views"] = form_view
        action["res_id"] = self.new_picking_id.id
        return action
