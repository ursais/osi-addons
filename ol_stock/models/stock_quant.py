from odoo import fields, models
from odoo.addons.stock_inventory.models.stock_quant import StockQuant


# Override _apply_inventory in stock_quant module to fix the link issue of stock move.


def _apply_inventory(self):
    res = super(StockQuant, self)._apply_inventory()

    record_moves = self.env["stock.move.line"]
    adjustment = self.env["stock.inventory"].browse()
    for rec in self:
        adjustment = rec.current_inventory_id
        moves = record_moves.search(
            [
                ("product_id", "=", rec.product_id.id),
                ("lot_id", "=", rec.lot_id.id),
                "|",
                ("location_id", "=", rec.location_id.id),
                ("location_dest_id", "=", rec.location_id.id),
            ],
            order="id asc",
        ).filtered(
            lambda x, rec=rec: not x.company_id.id
            or not rec.company_id.id
            or rec.company_id.id == x.company_id.id
        )
        if len(moves) == 0:
            raise ValueError(_("No move lines have been created"))
        move = moves[len(moves) - 1]
        adjustment.stock_move_ids |= move
        reference = move.reference
        if adjustment.name and move.reference:
            reference = adjustment.name + ": " + move.reference
        elif adjustment.name:
            reference = adjustment.name
        move.write(
            {
                "inventory_adjustment_id": adjustment.id,
                "reference": reference,
            }
        )
        rec.to_do = False
        rec.current_inventory_id = False
    if adjustment and self.env.company.stock_inventory_auto_complete:
        adjustment.action_auto_state_to_done()
    return res


# Apply the override
StockQuant._apply_inventory = _apply_inventory
