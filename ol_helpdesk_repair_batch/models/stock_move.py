# Import Odoo libs
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # COLUMNS ###

    repair_batch_line_id = fields.Many2one(
        comodel_name="repair.batch.line",
        string="Repair Batch Line",
        ondelete="cascade",
    )

    # END #######
    # METHODS ###

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if (
                move.repair_id
                and move.repair_id.state == "under_repair"
                and move.repair_line_type == "add"
            ):
                move.repair_id._create_or_update_internal_transfer()
        return moves

    def write(self, vals):
        res = super().write(vals)
        # Trigger only if relevant fields changed
        watched_fields = {"product_id", "product_uom_qty", "state", "type", "repair_id"}
        if watched_fields.intersection(vals.keys()):
            for move in self:
                if (
                    move.repair_id
                    and move.repair_id.state == "under_repair"
                    and move.repair_line_type == "add"
                ):
                    move.repair_id._create_or_update_internal_transfer()
        return res

    def unlink(self):
        repairs = self.mapped("repair_id").filtered(lambda r: r.state == "under_repair")
        res = super().unlink()
        for repair in repairs:
            repair._create_or_update_internal_transfer()
        return res

    # END #######
