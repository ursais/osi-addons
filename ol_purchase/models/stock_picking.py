# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """
    Extend Stock Picking:
    - Add date_approve field related to PO
    - When Scheduled Date (date_deadline) is changed on a receipt picking,
      update the same field on its non-done/cancelled moves.
    """

    _inherit = "stock.picking"

    # COLUMNS ##########

    date_approve = fields.Datetime(
        string="Confirmation Date",
        related="move_ids.purchase_line_id.order_id.date_approve",
    )

    # END ##########
    # METHODS ######

    @api.depends(
        "move_ids.date_deadline",
        "move_type",
    )
    def _compute_date_deadline(self):
        # Exclude incoming pickings from the default computation of date_deadline
        records = self.filtered(lambda l: l.picking_type_code != "incoming")

        # Call the parent method only for non-incoming pickings
        return super(StockPicking, records)._compute_date_deadline()

    def write(self, vals):
        """
        Now that date_deadline is editable on IN's, we need to update
        moves when it gets changed.
        """
        res = super().write(vals)

        if "date_deadline" in vals:
            for picking in self:
                if picking.picking_type_code != "incoming":
                    continue

                move_to_update = picking.move_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )
                if move_to_update:
                    move_to_update.write({"date_deadline": vals["date_deadline"]})

        return res

    # END ##########
