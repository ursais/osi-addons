# Import Odoo Libs
from odoo import _, api, fields, models
from odoo.addons.repair.models.stock_move import StockMove
from odoo.exceptions import ValidationError


# Override _clean_repair_sale_order_line in repair module to reduce database writes
# Improves sale order confirm speed
def _clean_repair_sale_order_line(self):
    lines = self.filtered(lambda m: m.repair_id and m.sale_line_id).mapped(
        "sale_line_id"
    )
    if lines:
        lines.write({"product_uom_qty": 0.0})


# Apply the override
StockMove._clean_repair_sale_order_line = _clean_repair_sale_order_line


class StockMove(models.Model):
    _inherit = "stock.move"

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # Add index to bom_line_id to improve speed, particularly when
    # stock moves are deleted.
    bom_line_id = fields.Many2one(
        comodel_name="mrp.bom.line",
        string="BoM Line",
        check_company=True,
        index=True,
    )

    # END #########

    # METHODS #####

    @api.constrains("quantity")
    def _check_quantity(self):
        """Ensure that the received quantity does not exceed the demanded quantity
          for incoming pickings that are not yet done.
        """
        for rec in self.filtered(
            lambda l: l.picking_code == "incoming"
            and l.state != "done"
            and l.quantity > l.product_uom_qty
        ):
            raise ValidationError(
                _(
                    "You cannot exceed demand quantity for product:-\n%s",
                    rec.product_id.name,
                )
            )

    def unlink(self):
        for move in self:
            picking = move.picking_id
            if (
                picking
                and picking.picking_type_id.code == 'outgoing' and picking.sale_id
                and not self.env.user.has_group('ol_stock.group_allow_add_delete_line_out')
            ):
                raise ValidationError(_(
                    "You are not allowed to delete stock moves for outgoing transfers "
                    "that are linked to a sale order."
                ))
        
        return super(StockMove, self).unlink()
    

    # END #########
