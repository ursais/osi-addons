# Import Odoo libs
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # COLUMNS ###

    is_repair_component = fields.Boolean(
        string="Repair Component",
        help="Technical field to mark lines that come from repair added parts.",
    )
    repair_ids = fields.Many2many(
        comodel_name="repair.order",
        string="Repairs",
        help="Repairs that generated this line. Used to source stock from the repair location.",
    )

    # END #######
    # METHODS ###

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        # Skip stock rules for repair component lines (like in core repair)
        lines_without_repair_parts = self.filtered(lambda l: not l.is_repair_component)
        return super(
            SaleOrderLine, lines_without_repair_parts
        )._action_launch_stock_rule(previous_product_uom_qty)

    def _prepare_procurement_values(self, group_id=False):
        """
        Extend procurement values to source stock from repairs.

        - If the line is linked to repairs, use the repair's location as the source location
        (when all repairs share the same location).
        - If all repairs have the same owner, enforce that owner on the move.
        - Clear route_ids to prevent manufacturing orders from being created.
        """
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.repair_ids:
            repair_locations = self.repair_ids.mapped("location_id")
            if len(repair_locations) == 1:
                vals["location_id"] = repair_locations.id

            # Ensure owner consistency
            owners = self.repair_ids.mapped("partner_id")
            if len(owners) == 1:
                vals["owner_id"] = owners.id

            # Prevent MO creation
            vals["route_ids"] = self.env["stock.route"].browse()
        return vals

    # END #######
