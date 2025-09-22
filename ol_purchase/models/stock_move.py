# Import Odoo libs
from odoo import fields, models


class StockMove(models.Model):
    """Inherit stock move to update PO dates if dates change on Receipt moves"""

    _inherit = "stock.move"

    # METHODS #####

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get("skip_po_sync"):
            return res

        if not {"date", "date_deadline"} & set(vals.keys()):
            return res

        moves = self.filtered(
            lambda m: m.picking_code == "incoming"
            and m.purchase_line_id
            and m.state not in ("done", "cancel")
        )
        if not moves:
            return res

        for pol in moves.mapped("purchase_line_id"):
            open_incoming_moves = pol.move_ids.filtered(
                lambda mv: mv.picking_code == "incoming"
                and mv.state not in ("done", "cancel")
            )
            candidates = open_incoming_moves.mapped(
                "date_deadline"
            ) or open_incoming_moves.mapped("date")
            if not candidates:
                continue

            new_date = max(candidates)
            if pol.date_planned and fields.Datetime.to_datetime(
                pol.date_planned
            ) == fields.Datetime.to_datetime(new_date):
                continue

            pol.with_context(skip_move_sync=True).write({"date_planned": new_date})

        return res

    # END #########
